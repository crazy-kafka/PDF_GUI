import os
import subprocess

from PyQt5.QtCore import QSettings, QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (QAbstractItemView, QHeaderView, QMenu,
                             QTableWidget, QTableWidgetItem)

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import StepStatus, Version


class MetricTable(QTableWidget):
    def __init__(self, version: Version, config: FlowConfig, parent=None):
        columns = ["Step"] + [m.label for m in config.metrics] + \
                  [c.label for c in config.job_columns]
        super().__init__(len(version.steps), len(columns), parent)
        self._version = version
        self._config = config
        self._columns = columns

        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
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

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        height = self.horizontalHeader().height() + 4
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        self.setFixedHeight(height)

    def _fill_data(self):
        icon_map = {
            StepStatus.SUCCESS: self._config.icons.SUCCESS,
            StepStatus.FAIL: self._config.icons.FAIL,
            StepStatus.RUNNING: self._config.icons.RUNNING,
            StepStatus.PENDING: self._config.icons.PENDING,
        }
        sc_map = {sc.name: sc for sc in self._config.steps}

        for row, step in enumerate(self._version.steps):
            sc = sc_map.get(step.name)
            label = sc.label if sc else step.name
            self.setItem(row, 0, QTableWidgetItem(label))

            for col, mc in enumerate(self._config.metrics, start=1):
                val = step.metrics.get(mc.key)
                if val is None:
                    self.setItem(row, col, QTableWidgetItem("—"))
                else:
                    text = format(val, mc.format)
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(row, col, item)

            for col, jc in enumerate(
                    self._config.job_columns,
                    start=1 + len(self._config.metrics)):
                if step.job is None:
                    self.setItem(row, col, QTableWidgetItem("—"))
                elif jc.key == "status":
                    icon = icon_map.get(step.status, "?")
                    self.setItem(row, col, QTableWidgetItem(
                        f"{icon} {step.status.value}"))
                else:
                    val = getattr(step.job, jc.key, "")
                    self.setItem(row, col, QTableWidgetItem(str(val)))

    def _resolve_report_paths(self, row: int, metric_idx: int) -> list[tuple[str, str]]:
        """Return list of (display_path, full_resolved_path) for a cell."""
        step_name = self._version.steps[row].name
        mc = self._config.metrics[metric_idx]
        result = []
        for report_path in mc.reports:
            resolved = report_path.replace("{version}", self._version.name)
            resolved = resolved.replace("{step}", step_name)
            resolved = resolved.replace("{run_dir}", self._version.dir_path)
            full_path = resolved if os.path.isabs(resolved) else os.path.normpath(
                os.path.join(self._version.dir_path, resolved))
            result.append((report_path, full_path))
        return result

    def _get_report_command(self) -> str:
        settings = QSettings("pdf_gui", "settings")
        gui_cmd = settings.value("report_command", "")
        if gui_cmd:
            return gui_cmd
        return self._config.report_command

    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item is None:
            return
        col = item.column()
        metric_idx = col - 1
        if metric_idx < 0 or metric_idx >= len(self._config.metrics):
            return

        row = item.row()
        if row >= len(self._version.steps):
            return

        mc = self._config.metrics[metric_idx]
        if not mc.reports:
            return

        paths = self._resolve_report_paths(row, metric_idx)
        if not paths:
            return

        menu = QMenu(self)
        for display_path, full_path in paths:
            action = menu.addAction(display_path)
            action.setData(full_path)

        action = menu.exec_(self.viewport().mapToGlobal(pos))
        if action:
            file_path = action.data()
            cmd = self._get_report_command()
            if cmd:
                subprocess.Popen(
                    cmd.replace("{file}", file_path),
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif os.path.isfile(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
