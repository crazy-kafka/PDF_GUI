import os
import subprocess

from PyQt5.QtCore import QSettings, QUrl, Qt
from PyQt5.QtGui import QColor, QDesktopServices, QFont
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QFrame, QHeaderView,
                             QMenu, QPushButton, QTableWidget,
                             QTableWidgetItem)

from pdf_gui.models.config import FlowConfig, StepGroupConfig
from pdf_gui.models.run_data import GroupedVersion, StepStatus, Version
from pdf_gui.utils.log import get_logger

log = get_logger()


class MetricTable(QTableWidget):
    def __init__(self, gv: GroupedVersion, config: FlowConfig,
                 group: StepGroupConfig = None, parent=None):
        self._gv = gv
        self._config = config
        self._group = group
        self._has_logs = any(sc.logs for g in config.step_groups for sc in g.steps)

        eff_metrics = group.metrics if group else config.step_groups[0].metrics
        columns = ["Step"] + [m.label for m in eff_metrics] + \
                  [c.label for c in config.job_columns]
        if self._has_logs:
            columns.append("Log")
        self._columns = columns

        super().__init__(len(gv.steps), len(columns), parent)

        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setVisible(False)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.NoFrame)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

        self._fill_data()

        self.resizeColumnsToContents()
        for col in range(self.columnCount()):
            if self.columnWidth(col) < 55:
                self.setColumnWidth(col, 55)
        if self.columnCount() > 0:
            self.setColumnWidth(0, max(self.columnWidth(0), 70))
        if self._has_logs:
            log_col = self.columnCount() - 1
            self.setColumnWidth(log_col, 55)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        height = self.horizontalHeader().height() + 4
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        self.setFixedHeight(height)

    def resize_for_font(self):
        """Recompute column widths and table height after font change."""
        self.resizeColumnsToContents()
        for col in range(self.columnCount()):
            if self.columnWidth(col) < 55:
                self.setColumnWidth(col, 55)
        if self.columnCount() > 0:
            self.setColumnWidth(0, max(self.columnWidth(0), 70))
        if self._has_logs:
            self.setColumnWidth(self.columnCount() - 1, 55)
        height = self.horizontalHeader().height() + 4
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        self.setFixedHeight(height)

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
            subprocess.Popen(
                cmd.replace("{file}", file_path),
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
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
        log_col = self.columnCount() - 1 if self._has_logs else -1

        for row, step in enumerate(self._gv.steps):
            sc = sc_map.get(step.name)
            label = sc.label if sc else step.name
            self.setItem(row, 0, QTableWidgetItem(label))

            for col, mc in enumerate(eff_metrics, start=1):
                val = step.metrics.get(mc.key)
                if val is None:
                    self.setItem(row, col, QTableWidgetItem("—"))
                else:
                    text = format(val, mc.format)
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(row, col, item)

            for col, jc in enumerate(
                    self._config.job_columns, start=job_start):
                if step.job is None:
                    self.setItem(row, col, QTableWidgetItem("—"))
                elif jc.key == "status":
                    icon = icon_map.get(step.status, "?")
                    item = QTableWidgetItem(f"{icon} {step.status.value}")
                    item.setForeground(color_map.get(step.status, QColor("#000")))
                    self.setItem(row, col, item)
                else:
                    val = getattr(step.job, jc.key, "")
                    self.setItem(row, col, QTableWidgetItem(str(val)))

            if self._has_logs and sc and sc.logs:
                btn = QPushButton("Log")
                btn.setFixedHeight(40)
                btn.clicked.connect(
                    lambda checked, r=row: self._on_log_clicked(r))
                self.setCellWidget(row, log_col, btn)

    # ── log button ──────────────────────────────────────────────────

    def _on_log_clicked(self, row: int):
        step = self._gv.steps[row]
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

        row = item.row()
        if row >= len(self._gv.steps):
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
