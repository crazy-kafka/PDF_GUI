from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QVBoxLayout, QWidget)

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import OverallStatus, Version

STATUS_COLOR_MAP = {
    OverallStatus.SUCCESS: "#4CAF50",
    OverallStatus.RUNNING: "#2196F3",
    OverallStatus.FAIL: "#F44336",
}

SIDEBAR_WIDTH = 230
ITEM_MAX_NAME_WIDTH = 185


class Sidebar(QWidget):
    version_selected = pyqtSignal(str)

    def __init__(self, config: FlowConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setMaximumWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("VERSIONS")
        header.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setUniformItemSizes(True)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

    def rebuild(self, versions: list[Version]):
        self._list.clear()
        for v in versions:
            item = QListWidgetItem()
            widget = self._make_item_widget(v)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, v.name)
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)

    def _make_item_widget(self, version: Version) -> QWidget:
        dot_color = STATUS_COLOR_MAP.get(version.status, "#9E9E9E")
        icon = self._config.icons.SUCCESS
        if version.status == OverallStatus.FAIL:
            icon = self._config.icons.FAIL
        elif version.status == OverallStatus.RUNNING:
            icon = self._config.icons.RUNNING

        widget = QWidget()
        widget.setFixedHeight(44)
        widget.setToolTip(version.name)

        hlayout = QHBoxLayout(widget)
        hlayout.setContentsMargins(4, 2, 4, 2)
        hlayout.setSpacing(4)

        dot = QLabel(f'<span style="color:{dot_color}; font-size:14px;">●</span> {icon}')
        dot.setFixedWidth(30)
        hlayout.addWidget(dot)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)

        name_label = QLabel(version.name)
        name_label.setStyleSheet("font-weight: bold;")
        name_label.setMaximumWidth(ITEM_MAX_NAME_WIDTH)
        name_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        fm = name_label.fontMetrics()
        name_label.setText(fm.elidedText(version.name, Qt.ElideRight, ITEM_MAX_NAME_WIDTH))

        subtitle = f"{version.latest_step} · {version.status.value}" if version.latest_step else version.status.value
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet("color: #555; font-size: 11px;")
        sub_label.setMaximumWidth(ITEM_MAX_NAME_WIDTH)
        fm_sub = sub_label.fontMetrics()
        sub_label.setText(fm_sub.elidedText(subtitle, Qt.ElideRight, ITEM_MAX_NAME_WIDTH))

        text_layout.addWidget(name_label)
        text_layout.addWidget(sub_label)
        hlayout.addLayout(text_layout)
        hlayout.addStretch()

        return widget

    def _on_item_clicked(self, item: QListWidgetItem):
        name = item.data(Qt.UserRole)
        if name:
            self.version_selected.emit(name)
