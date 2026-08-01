from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget)

from pdf_gui.models.config import FlowConfig, StepGroupConfig
from pdf_gui.models.run_data import GroupedVersion, OverallStatus, Version
from pdf_gui.widgets.metric_table import MetricTable
from pdf_gui import theme


class VersionPanel(QWidget):
    def __init__(self, gv: GroupedVersion, config: FlowConfig,
                 group: StepGroupConfig = None, parent=None):
        super().__init__(parent)
        self._gv = gv
        self._config = config
        self._group = group
        self._collapsed = False

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 2)
        layout.setSpacing(0)

        header = self._make_header()
        layout.addWidget(header)

        self._table = MetricTable(self._gv, self._config,
                                  group=self._group)
        layout.addWidget(self._table)

    def _make_header(self) -> QFrame:
        color = theme.header_color(self._config.colors, self._gv.status)
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setStyleSheet(
            f"QFrame {{ background-color: {color}; border-radius: 4px; }}"
        )
        frame.setFixedHeight(32)
        frame.setContentsMargins(0, 0, 0, 0)

        hlayout = QHBoxLayout(frame)
        hlayout.setContentsMargins(8, 2, 8, 2)

        self._fold_btn = QPushButton("−")
        self._fold_btn.setFixedSize(24, 24)
        self._fold_btn.clicked.connect(self._toggle_fold)
        hlayout.addWidget(self._fold_btn)

        name = self._gv.name
        name_label = QLabel(f"Version: {name}")
        name_label.setStyleSheet(
            f"color: {theme.get_theme().header_text}; font-weight: bold;")
        name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        hlayout.addWidget(name_label)

        hlayout.addStretch()

        icon = self._config.icons.SUCCESS
        if self._gv.status == OverallStatus.FAIL:
            icon = self._config.icons.FAIL
        elif self._gv.status == OverallStatus.RUNNING:
            icon = self._config.icons.RUNNING
        elif self._gv.status == OverallStatus.PENDING:
            icon = self._config.icons.PENDING
        status_label = QLabel(f"{icon} {self._gv.status.value}")
        status_label.setStyleSheet(
            f"color: {theme.get_theme().header_text}; font-weight: bold;")
        hlayout.addWidget(status_label)

        return frame

    def _toggle_fold(self):
        self._collapsed = not self._collapsed
        self._table.setVisible(not self._collapsed)
        self._fold_btn.setText("+" if self._collapsed else "−")

    def resize_for_font(self, data_family: str, size: int):
        self._table.resize_for_font(data_family, size)

    def table_width(self) -> int:
        """Total width of all table columns (content width, not viewport)."""
        return self._table.horizontalHeader().length()

    def is_collapsed(self) -> bool:
        return self._collapsed

    def set_collapsed(self, collapsed: bool):
        if collapsed != self._collapsed:
            self._toggle_fold()

    def version_name(self) -> str:
        return self._gv.name
