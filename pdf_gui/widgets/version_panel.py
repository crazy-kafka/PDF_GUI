from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget)

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import OverallStatus, Version
from pdf_gui.widgets.metric_table import MetricTable

STATUS_COLOR_MAP = {
    OverallStatus.SUCCESS: "#2E7D32",
    OverallStatus.RUNNING: "#1565C0",
    OverallStatus.FAIL: "#C62828",
    OverallStatus.PENDING: "#E65100",
}


class VersionPanel(QWidget):
    def __init__(self, version: Version, config: FlowConfig, parent=None):
        super().__init__(parent)
        self._version = version
        self._config = config
        self._collapsed = False

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(0)

        header = self._make_header()
        layout.addWidget(header)

        self._table = MetricTable(self._version, self._config)
        layout.addWidget(self._table)

    def _make_header(self) -> QFrame:
        color = STATUS_COLOR_MAP.get(self._version.status, "#757575")
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {color}; border-radius: 4px; }}"
        )
        frame.setFixedHeight(32)

        hlayout = QHBoxLayout(frame)
        hlayout.setContentsMargins(8, 2, 8, 2)

        self._fold_btn = QPushButton("−")
        self._fold_btn.setFixedSize(24, 24)
        self._fold_btn.clicked.connect(self._toggle_fold)
        hlayout.addWidget(self._fold_btn)

        fm = QFontMetrics(self.font())
        name = self._version.name
        elided = fm.elidedText(f"Version: {name}", Qt.ElideRight, 800)
        name_label = QLabel(elided)
        name_label.setStyleSheet("color: white; font-weight: bold;")
        name_label.setToolTip(name)
        hlayout.addWidget(name_label)

        hlayout.addStretch()

        icon = self._config.icons.SUCCESS
        if self._version.status == OverallStatus.FAIL:
            icon = self._config.icons.FAIL
        elif self._version.status == OverallStatus.RUNNING:
            icon = self._config.icons.RUNNING
        elif self._version.status == OverallStatus.PENDING:
            icon = self._config.icons.PENDING
        status_label = QLabel(f"{icon} {self._version.status.value}")
        status_label.setStyleSheet("color: white; font-weight: bold;")
        hlayout.addWidget(status_label)

        return frame

    def _toggle_fold(self):
        self._collapsed = not self._collapsed
        self._table.setVisible(not self._collapsed)
        self._fold_btn.setText("+" if self._collapsed else "−")

    def is_collapsed(self) -> bool:
        return self._collapsed

    def set_collapsed(self, collapsed: bool):
        if collapsed != self._collapsed:
            self._toggle_fold()

    def version_name(self) -> str:
        return self._version.name
