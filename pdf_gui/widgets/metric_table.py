import os
import shlex
import subprocess

from PyQt5.QtCore import QSettings, QUrl, Qt
from PyQt5.QtGui import QColor, QDesktopServices, QFont, QPen
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QFrame, QHeaderView,
                             QMenu, QPushButton, QStyledItemDelegate,
                             QTableWidget, QTableWidgetItem)

from pdf_gui.models.config import FlowConfig, StepGroupConfig
from pdf_gui.models.run_data import GroupedVersion, StepStatus, Version
from pdf_gui.utils.log import get_logger
from pdf_gui import theme

log = get_logger()


class MetricBorderDelegate(QStyledItemDelegate):
    """Emphasize boundaries between metrics without changing group internals."""

    def __init__(self, table, parent=None):
        super().__init__(parent)
        self._table = table

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        if not self._table._is_metric_start(index.column()):
            return

        painter.save()
        painter.setPen(QPen(QColor(theme.get_theme().metric_separator), 2))
        x = option.rect.left()
        painter.drawLine(x, option.rect.top(), x, option.rect.bottom())
        painter.restore()


class MetricTable(QTableWidget):
    def __init__(self, gv: GroupedVersion, config: FlowConfig,
                 group: StepGroupConfig = None, parent=None):
        self._gv = gv
        self._config = config
        self._group = group
        self._has_logs = any(sc.logs for g in config.step_groups for sc in g.steps)
        self._has_databases = any(sc.databases for g in config.step_groups for sc in g.steps)
        eff_metrics = group.metrics if group else config.step_groups[0].metrics

        # parse @-grouped metrics
        self._metric_groups = {}  # prefix → (start_col, sub_labels)
        col_idx = 1  # col 0 = Step
        for m in eff_metrics:
            if "@" in m.key:
                prefix = m.key.split("@", 1)[0]
                if prefix not in self._metric_groups:
                    self._metric_groups[prefix] = (col_idx, [])
                self._metric_groups[prefix][1].append(m.label)
            col_idx += 1
        self._has_grouped_header = bool(self._metric_groups)
        self._data_row_offset = 2 if self._has_grouped_header else 0

        columns = ["Step"] + [m.label for m in eff_metrics] + \
                  [c.label for c in config.job_columns]
        if self._has_logs:
            columns.append("Log")
        if self._has_databases:
            columns.append("DB")
        self._columns = columns
        total_cols = len(columns)
        total_rows = len(gv.steps) + self._data_row_offset

        super().__init__(total_rows, total_cols, parent)

        if self._has_grouped_header:
            self.horizontalHeader().setVisible(False)
        else:
            self.setHorizontalHeaderLabels(columns)
        self.verticalHeader().setVisible(False)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.NoFrame)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        self._metric_end_col = 1 + len(eff_metrics)
        self._metric_separator_cols = {
            col for col in range(1, self._metric_end_col)
            if col == 1 or not self._same_metric_group(col - 1, col, eff_metrics)
        }
        self.setItemDelegate(MetricBorderDelegate(self, self))
        self._data_font = QFont(config.data_font, config.default_font_size)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

        if self._has_grouped_header:
            self._build_grouped_header(eff_metrics)

        self._fill_data()

        self._apply_column_widths()
        self._apply_fixed_height()

    def _same_metric_group(self, left_col, right_col, metrics):
        left_key = metrics[left_col - 1].key
        right_key = metrics[right_col - 1].key
        if "@" not in left_key or "@" not in right_key:
            return False
        return left_key.split("@", 1)[0] == right_key.split("@", 1)[0]

    def _is_metric_start(self, column):
        """Return whether a column should receive a strong left border."""
        return column in self._metric_separator_cols

    def _build_grouped_header(self, eff_metrics):
        """Render two-row header with parent group labels spanning sub-columns."""
        hdr_fill = QColor(theme.get_theme().table_header_bg)
        hdr_font_w = QFont()
        hdr_font_w.setBold(True)
        hdr_fg = QColor(theme.get_theme().text_primary)

        def _hdr_cell(text, row, col):
            item = QTableWidgetItem(text)
            item.setBackground(hdr_fill)
            item.setForeground(hdr_fg)
            item.setFont(hdr_font_w)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        # Row 0: Step (span 2 rows)
        _hdr_cell("Step", 0, 0)
        self.setSpan(0, 0, 2, 1)

        # Row 0: group parent labels
        for prefix, (start_col, sub_labels) in self._metric_groups.items():
            n = len(sub_labels)
            _hdr_cell(prefix, 0, start_col)
            if n > 1:
                self.setSpan(0, start_col, 1, n)
            else:
                self.setSpan(0, start_col, 2, 1)

        # Row 0: ungrouped metrics (span 2 rows)
        col = 1
        for m in eff_metrics:
            if "@" not in m.key:
                _hdr_cell(m.label, 0, col)
                self.setSpan(0, col, 2, 1)
            col += 1

        # Row 0: job columns + log (span 2 rows)
        for jc in self._config.job_columns:
            _hdr_cell(jc.label, 0, col)
            self.setSpan(0, col, 2, 1)
            col += 1
        if self._has_logs:
            _hdr_cell("Log", 0, col)
            self.setSpan(0, col, 2, 1)
            col += 1
        if self._has_databases:
            _hdr_cell("DB", 0, col)
            self.setSpan(0, col, 2, 1)
            col += 1

        # Row 1: sub-labels for grouped metrics
        for prefix, (start_col, sub_labels) in self._metric_groups.items():
            for j, sub in enumerate(sub_labels):
                _hdr_cell(sub, 1, start_col + j)

        # Row 1: set items for spanned cells too (to avoid empty items)
        for col in range(self.columnCount()):
            if self.item(1, col) is None:
                self.setItem(1, col, QTableWidgetItem(""))

    def _apply_column_widths(self):
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # Temporarily clear group parent labels so resizeColumnsToContents()
        # sizes columns by sub-label + data width, not by long parent names
        saved = {}
        if self._has_grouped_header:
            for prefix, (start_col, _) in self._metric_groups.items():
                item = self.item(0, start_col)
                if item:
                    saved[start_col] = item.text()
                    item.setText("")
        self.resizeColumnsToContents()
        # Restore group parent labels
        for col, text in saved.items():
            self.item(0, col).setText(text)
        for col in range(self.columnCount()):
            if self.columnWidth(col) < 55:
                self.setColumnWidth(col, 55)
        if self.columnCount() > 0:
            self.setColumnWidth(0, max(self.columnWidth(0), 70))
        if self._has_logs:
            self.setColumnWidth(self.columnCount() - (1 if self._has_databases else 0) - 1, 55)
        if self._has_databases:
            self.setColumnWidth(self.columnCount() - 1, 45)

    def _apply_fixed_height(self):
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        height = 0
        if not self._has_grouped_header:
            height += self.horizontalHeader().height()
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        height += 4  # frame border allowance
        self.setFixedHeight(height)

    def resize_for_font(self, data_family: str, size: int):
        """Apply new data font to all cells, then recompute sizes."""
        self._data_font = QFont(data_family, size)
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item is not None:
                    item.setFont(self._data_font)
        self._apply_column_widths()
        self._apply_fixed_height()

    # ── path resolution ────────────────────────────────────────────

    def _resolve_paths(self, paths: list[str],
                       step_name: str) -> list[tuple[str, str]]:
        """Return list of (display_path, full_resolved_path) for template paths."""
        result = []
        for p in paths:
            resolved = p.replace("{version}", self._gv.name)
            resolved = resolved.replace("{step}", step_name)
            resolved = resolved.replace("{run_dir}", self._gv.dir_path)
            full_path = resolved if os.path.isabs(resolved) else os.path.normpath(
                os.path.join(self._gv.dir_path, resolved))
            result.append((p, full_path))
        return result

    def _get_report_command(self) -> str:
        settings = QSettings("pdf_gui", "settings")
        gui_cmd = settings.value("report_command", "")
        if gui_cmd:
            return gui_cmd
        return self._config.report_command

    def _get_picture_command(self) -> str:
        settings = QSettings("pdf_gui", "settings")
        gui_cmd = settings.value("picture_command", "")
        if gui_cmd:
            return gui_cmd
        return self._config.picture_command

    def _open_file(self, file_path: str, file_type: str = "report"):
        cmd = self._get_picture_command() if file_type == "picture" else self._get_report_command()
        if cmd:
            args = shlex.split(cmd.replace("{file}", file_path))
            subprocess.Popen(args, shell=False,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os.path.isfile(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            log.warning("File not found: %s", file_path)

    # ── data fill ───────────────────────────────────────────────────

    def _fill_data(self):
        icon_map = {
            StepStatus.SUCCESS: self._config.icons.SUCCESS,
            StepStatus.FAIL: self._config.icons.FAIL,
            StepStatus.RUNNING: self._config.icons.RUNNING,
            StepStatus.PENDING: self._config.icons.PENDING,
        }
        color_map = {
            StepStatus.SUCCESS: QColor(self._config.colors.SUCCESS),
            StepStatus.FAIL: QColor(self._config.colors.FAIL),
            StepStatus.RUNNING: QColor(self._config.colors.RUNNING),
            StepStatus.PENDING: QColor(self._config.colors.PENDING),
        }
        sc_map = {}
        for g in self._config.step_groups:
            for sc in g.steps:
                if sc.name not in sc_map:
                    sc_map[sc.name] = sc

        eff_metrics = self._group.metrics if self._group else self._config.step_groups[0].metrics
        metric_count = len(eff_metrics)
        job_start = 1 + metric_count
        log_col = self.columnCount() - (1 if self._has_databases else 0) - 1 if self._has_logs else -1
        db_col = self.columnCount() - 1 if self._has_databases else -1

        for row, step in enumerate(self._gv.steps, start=self._data_row_offset):
            sc = sc_map.get(step.name)
            label = sc.label if sc else step.name
            step_item = QTableWidgetItem(label)
            step_item.setFont(self._data_font)
            self.setItem(row, 0, step_item)

            for col, mc in enumerate(eff_metrics, start=1):
                val = step.metrics.get(mc.key)
                if val is None:
                    item = QTableWidgetItem("—")
                else:
                    text = format(val, mc.format)
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item.setFont(self._data_font)
                self.setItem(row, col, item)

            for col, jc in enumerate(
                    self._config.job_columns, start=job_start):
                if step.job is None:
                    item = QTableWidgetItem("—")
                elif jc.key == "status":
                    icon = icon_map.get(step.status, "?")
                    item = QTableWidgetItem(f"{icon} {step.status.value}")
                    item.setForeground(color_map.get(step.status, QColor(theme.get_theme().text_primary)))
                else:
                    val = getattr(step.job, jc.key, "")
                    item = QTableWidgetItem(str(val))
                item.setFont(self._data_font)
                self.setItem(row, col, item)

            if self._has_logs and sc and sc.logs:
                btn = QPushButton("Log")
                btn.setFixedHeight(40)
                btn.clicked.connect(
                    lambda checked, r=row: self._on_log_clicked(r))
                self.setCellWidget(row, log_col, btn)

            if self._has_databases and sc and sc.databases:
                btn = QPushButton("DB")
                btn.setFixedHeight(40)
                btn.clicked.connect(
                    lambda checked, r=row: self._on_db_clicked(r))
                self.setCellWidget(row, db_col, btn)

    # ── log button ──────────────────────────────────────────────────

    def _on_log_clicked(self, row: int):
        step = self._gv.steps[row - self._data_row_offset]
        sc_map = {}
        for g in self._config.step_groups:
            for sc in g.steps:
                if sc.name not in sc_map:
                    sc_map[sc.name] = sc
        sc = sc_map.get(step.name)
        if not sc or not sc.logs:
            return
        paths = self._resolve_paths(sc.logs, step.name)
        if len(paths) == 1:
            self._open_file(paths[0][1])
        elif paths:
            menu = QMenu(self)
            for display_path, full_path in paths:
                action = menu.addAction(display_path)
                action.setData(full_path)
            btn = self.sender()
            if isinstance(btn, QPushButton):
                pos = btn.mapToGlobal(btn.rect().bottomLeft())
            else:
                pos = self.viewport().mapToGlobal(
                    self.visualItemRect(self.item(row, 0)).bottomLeft())
            action = menu.exec_(pos)
            if action:
                self._open_file(action.data())

    # ── database button ──────────────────────────────────────────────

    def _on_db_clicked(self, row: int):
        step_idx = row - self._data_row_offset
        if step_idx < 0 or step_idx >= len(self._gv.steps):
            return
        step = self._gv.steps[step_idx]
        sc_map = {}
        for g in self._config.step_groups:
            for sc in g.steps:
                if sc.name not in sc_map:
                    sc_map[sc.name] = sc
        sc = sc_map.get(step.name)
        if not sc or not sc.databases:
            return

        if len(sc.databases) == 1:
            db = sc.databases[0]
            cmd = self._resolve_db_command(db, step.name)
            if cmd:
                self._launch_command(cmd)
            else:
                log.warning("No command for database '%s'", db.label)
        else:
            menu = QMenu(self)
            for db in sc.databases:
                action = menu.addAction(db.label)
                action.setData(db)
            btn = self.sender()
            if isinstance(btn, QPushButton):
                pos = btn.mapToGlobal(btn.rect().bottomLeft())
            else:
                pos = self.viewport().mapToGlobal(
                    self.visualItemRect(self.item(row, 0)).bottomLeft())
            action = menu.exec_(pos)
            if action:
                db = action.data()
                cmd = self._resolve_db_command(db, step.name)
                if cmd:
                    self._launch_command(cmd)
                else:
                    log.warning("No command for database '%s'", db.label)

    def _resolve_db_command(self, db, step_name: str) -> str:
        """Resolve a DatabaseConfig to a launch command string."""
        # Per-DB command takes priority
        template = db.command
        # Fall back to global/QSettings database_command
        if not template:
            template = self._get_database_command()
        if not template:
            return ""
        return (template
                .replace("{label}", db.label)
                .replace("{version}", self._gv.name)
                .replace("{step}", step_name)
                .replace("{run_dir}", self._gv.dir_path))

    def _get_database_command(self) -> str:
        settings = QSettings("pdf_gui", "settings")
        gui_cmd = settings.value("database_command", "")
        if gui_cmd:
            return gui_cmd
        return self._config.database_command

    def _launch_command(self, cmd: str):
        """Run a launch command via subprocess."""
        try:
            args = shlex.split(cmd)
            subprocess.Popen(args, shell=False,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.info("Launched: %s", cmd)
        except (OSError, ValueError) as e:
            log.error("Failed to launch command: %s — %s", cmd, e)

    # ── context menu (reports + pictures) ───────────────────────────

    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item is None:
            return
        col = item.column()
        metric_idx = col - 1
        eff_metrics = self._group.metrics if self._group else self._config.step_groups[0].metrics
        if metric_idx < 0 or metric_idx >= len(eff_metrics):
            return

        row = item.row() - self._data_row_offset
        if row < 0 or row >= len(self._gv.steps):
            return

        mc = eff_metrics[metric_idx]
        if not mc.reports and not mc.pictures:
            return

        step_name = self._gv.steps[row].name
        reports = mc.reports + mc.step_reports.get(step_name, [])
        pictures = mc.pictures + mc.step_pictures.get(step_name, [])
        report_paths = self._resolve_paths(reports, step_name)
        picture_paths = self._resolve_paths(pictures, step_name)

        menu = QMenu(self)
        bold_font = QFont()
        bold_font.setBold(True)

        if report_paths:
            header = QAction("Reports", menu)
            header.setFont(bold_font)
            header.setEnabled(False)
            menu.addAction(header)
            for display_path, full_path in report_paths:
                action = menu.addAction(os.path.basename(full_path))
                action.setData(("report", full_path))
                if not os.path.isfile(full_path):
                    action.setEnabled(False)

        if report_paths and picture_paths:
            menu.addSeparator()

        if picture_paths:
            header = QAction("Pictures", menu)
            header.setFont(bold_font)
            header.setEnabled(False)
            menu.addAction(header)
            for display_path, full_path in picture_paths:
                action = menu.addAction(os.path.basename(full_path))
                action.setData(("picture", full_path))
                if not os.path.isfile(full_path):
                    action.setEnabled(False)

        action = menu.exec_(self.viewport().mapToGlobal(pos))
        if action and action.isEnabled():
            data = action.data()
            file_type, file_path = data if isinstance(data, tuple) else ("report", data)
            self._open_file(file_path, file_type)
