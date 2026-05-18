import os

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (QAbstractItemView, QHeaderView, QMenu,
                             QTableWidget, QTableWidgetItem)

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import StepStatus, Version


class MetricTable(QTableWidget):
    def __init__(self, version: Version, config: FlowConfig, parent=None):
        columns = ["Step"] + [m.label for m in config.metrics] + \
                  [c.label for c in config.job_columns]
        super().__init__(len(config.steps), len(columns), parent)
        self._version = version
        self._config = config
        self._columns = columns

        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

        self._fill_data()

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        height = self.horizontalHeader().height() + 4
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        self.setFixedHeight(height)

    def _fill_data(self):
        step_map = {s.name: s for s in self._version.steps}
        icon_map = {
            StepStatus.SUCCESS: self._config.icons.SUCCESS,
            StepStatus.FAIL: self._config.icons.FAIL,
            StepStatus.RUNNING: self._config.icons.RUNNING,
            StepStatus.PENDING: self._config.icons.PENDING,
        }

        for row, sc in enumerate(self._config.steps):
            step = step_map.get(sc.name)
            self.setItem(row, 0, QTableWidgetItem(sc.label))

            if step is None:
                for col in range(1, len(self._columns)):
                    self.setItem(row, col, QTableWidgetItem("—"))
                continue

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

    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item is None:
            return
        col = item.column()
        metric_idx = col - 1
        if metric_idx < 0 or metric_idx >= len(self._config.metrics):
            return

        mc = self._config.metrics[metric_idx]
        if not mc.reports:
            return

        menu = QMenu(self)
        for report_path in mc.reports:
            full_path = os.path.join(self._version.dir_path, report_path)
            action = menu.addAction(report_path)
            action.setData(full_path)

        action = menu.exec_(self.viewport().mapToGlobal(pos))
        if action:
            file_path = action.data()
            if os.path.isfile(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
