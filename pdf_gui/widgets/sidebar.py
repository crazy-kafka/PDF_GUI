from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QVBoxLayout, QWidget)

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import OverallStatus, Version

STATUS_COLOR_MAP = {
    OverallStatus.SUCCESS: "#4CAF50",
    OverallStatus.RUNNING: "#2196F3",
    OverallStatus.FAIL: "#F44336",
    OverallStatus.PENDING: "#FF9800",
}


class Sidebar(QWidget):
    version_selected = pyqtSignal(str)

    def __init__(self, config: FlowConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self.setMinimumWidth(180)

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
        self._re_elide_all()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._re_elide_all()

    def _re_elide_all(self):
        available = self.width() - 50
        if available < 60:
            available = 60
        for i in range(self._list.count()):
            widget = self._list.itemWidget(self._list.item(i))
            if widget is None:
                continue
            name_label = widget.findChild(QLabel, "name_label")
            if name_label:
                fm = name_label.fontMetrics()
                full_name = widget.toolTip()
                name_label.setText(fm.elidedText(full_name, Qt.ElideRight, available))
            sub_step_label = widget.findChild(QLabel, "sub_step_label")
            if sub_step_label:
                fm = sub_step_label.fontMetrics()
                full_sub = sub_step_label.toolTip()
                sub_step_label.setText(fm.elidedText(full_sub, Qt.ElideRight,
                                                     max(available - 60, 30)))

    def _make_item_widget(self, version: Version) -> QWidget:
        dot_color = STATUS_COLOR_MAP.get(version.status, "#9E9E9E")
        icon = self._config.icons.SUCCESS
        if version.status == OverallStatus.FAIL:
            icon = self._config.icons.FAIL
        elif version.status == OverallStatus.RUNNING:
            icon = self._config.icons.RUNNING
        elif version.status == OverallStatus.PENDING:
            icon = self._config.icons.PENDING

        widget = QWidget()
        widget.setFixedHeight(44)
        widget.setToolTip(version.name)

        hlayout = QHBoxLayout(widget)
        hlayout.setContentsMargins(4, 2, 4, 2)
        hlayout.setSpacing(4)

        dot = QLabel(f'<span style="color:{dot_color}; font-size:20px;">●</span> {icon}')
        dot.setFixedWidth(40)
        hlayout.addWidget(dot)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)

        name_label = QLabel()
        name_label.setObjectName("name_label")
        name_label.setStyleSheet("font-weight: bold;")
        fm = name_label.fontMetrics()
        name_label.setText(fm.elidedText(version.name, Qt.ElideRight, self.width() - 50))

        sub_layout = QHBoxLayout()
        sub_layout.setSpacing(4)

        step_text = version.latest_step + " ·" if version.latest_step else ""
        sub_step_label = QLabel()
        sub_step_label.setObjectName("sub_step_label")
        sub_step_label.setStyleSheet("color: #888; font-size: 15px;")
        sub_step_label.setToolTip(step_text)
        fm_sub = sub_step_label.fontMetrics()
        sub_step_label.setText(fm_sub.elidedText(step_text, Qt.ElideRight, self.width() - 70))

        color = STATUS_COLOR_MAP.get(version.status, "#9E9E9E")
        sub_status_label = QLabel(version.status.value)
        sub_status_label.setObjectName("sub_status_label")
        sub_status_label.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold;")

        sub_layout.addWidget(sub_step_label)
        sub_layout.addWidget(sub_status_label)
        sub_layout.addStretch()

        text_layout.addWidget(name_label)
        text_layout.addLayout(sub_layout)
        hlayout.addLayout(text_layout)
        hlayout.addStretch()

        return widget

    def _on_item_clicked(self, item: QListWidgetItem):
        name = item.data(Qt.UserRole)
        if name:
            self.version_selected.emit(name)
