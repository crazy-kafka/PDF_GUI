from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QAction, QComboBox, QFontComboBox, QLabel,
                             QSizePolicy, QSpinBox, QToolBar, QWidget)

from pdf_gui import theme


class ToolbarWidget(QToolBar):
    refresh_clicked = pyqtSignal()
    font_changed = pyqtSignal(str, int)
    settings_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    sort_clicked = pyqtSignal()
    chart_clicked = pyqtSignal()
    theme_changed = pyqtSignal(str)

    def __init__(self, default_font: str = "Consolas",
                 default_font_size: int = 10,
                 data_font: str = "Consolas", parent=None):
        super().__init__("Toolbar", parent)
        self.setMovable(False)
        self.setObjectName("main_toolbar")

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_clicked.emit)
        self.addAction(refresh_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_clicked.emit)
        self.addAction(settings_action)

        export_action = QAction("Export", self)
        export_action.triggered.connect(self.export_clicked.emit)
        self.addAction(export_action)

        sort_action = QAction("Sort", self)
        sort_action.triggered.connect(self.sort_clicked.emit)
        self.addAction(sort_action)

        chart_action = QAction("Chart", self)
        chart_action.triggered.connect(self.chart_clicked.emit)
        self.addAction(chart_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        self.addWidget(QLabel("Font:"))

        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(default_font))
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        self.addWidget(self.font_combo)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(default_font_size)
        self.font_size.valueChanged.connect(self._on_font_changed)
        self.addWidget(self.font_size)

        self.addWidget(QLabel("Theme:"))

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(theme.theme_names())
        self.theme_combo.setCurrentText(theme.get_theme_name())
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.addWidget(self.theme_combo)

    def _on_font_changed(self):
        family = self.font_combo.currentFont().family()
        size = self.font_size.value()
        self.font_changed.emit(family, size)

    def _on_theme_changed(self, name):
        self.theme_changed.emit(name)
