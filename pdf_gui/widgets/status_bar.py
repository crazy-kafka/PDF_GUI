from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics


class StatusBar:
    def __init__(self, status_bar):
        self._bar = status_bar

    def update(self, version_count: int, latest_name: str):
        fm = QFontMetrics(self._bar.font())
        elided = fm.elidedText(latest_name, Qt.ElideRight, 300)
        self._bar.showMessage(f"{version_count} runs loaded | Latest: {elided}")
