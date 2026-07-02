"""Refresh progress overlay — "Silicon Pulse" effect.

A full-widget overlay shown during data refresh with a pulsing indicator
and progress text. Matches the Silicon Terminal dark theme.
"""

from PyQt5.QtCore import (QEasingCurve, QPoint, QPropertyAnimation, Qt,
                          pyqtProperty)
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from pdf_gui import theme


class PulseDot(QWidget):
    """A small circular indicator that pulses rhythmically."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._radius = 6.0
        self._anim = QPropertyAnimation(self, b"pulse_radius")
        self._anim.setDuration(1000)
        self._anim.setStartValue(6.0)
        self._anim.setEndValue(11.0)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setLoopCount(-1)  # infinite
        self._anim.start()

    def start_animation(self):
        if self._anim.state() != QPropertyAnimation.Running:
            self._anim.start()

    def stop_animation(self):
        if self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()

    @pyqtProperty(float)
    def pulse_radius(self):
        return self._radius

    @pulse_radius.setter
    def pulse_radius(self, r):
        self._radius = r
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        center = QPoint(self.width() // 2, self.height() // 2)
        r = int(self._radius)
        # Outer glow ring
        glow = QColor(theme.ThemeColors.text_secondary)
        glow.setAlpha(30)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(center, r + 4, r + 4)
        # Inner dot
        dot_color = QColor(theme.ThemeColors.text_primary)
        dot_color.setAlpha(220)
        p.setBrush(dot_color)
        p.drawEllipse(center, r, r)
        p.end()


class RefreshOverlay(QWidget):
    """Full-widget overlay with pulsing indicator and status text.

    Usage:
        overlay = RefreshOverlay(central_widget)
        overlay.show_with_message("Running refresh script...")
        # ... do work, call QApplication.processEvents() ...
        overlay.set_message("Loading version data...")
        # ... finish work ...
        overlay.hide()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("refresh_overlay")
        super().hide()

        # Semi-transparent dark backdrop
        self._backdrop = QColor(theme.ThemeColors.bg_deep)
        self._backdrop.setAlpha(220)

        # Block input during refresh
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Pulsing dot
        self._dot = PulseDot()
        layout.addWidget(self._dot, alignment=Qt.AlignCenter)

        # Status text
        self._label = QLabel("Refreshing...")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setFont(QFont("Segoe UI", 12))
        self._label.setStyleSheet(
            f"color: {theme.ThemeColors.text_primary}; "
            f"background: transparent; padding: 12px;"
        )
        layout.addWidget(self._label)

        # Sub-text (smaller, dimmer)
        self._sub_label = QLabel("")
        self._sub_label.setAlignment(Qt.AlignCenter)
        self._sub_label.setStyleSheet(
            f"color: {theme.ThemeColors.text_secondary}; "
            f"background: transparent; font-size: 10px;"
        )
        layout.addWidget(self._sub_label)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self._backdrop)
        p.end()

    def show_with_message(self, text: str, sub_text: str = ""):
        """Show the overlay with a status message."""
        self._label.setText(text)
        self._sub_label.setText(sub_text)
        self._sync_geometry()
        self.show()
        self.raise_()
        self._dot.start_animation()
        self.repaint()

    def set_message(self, text: str, sub_text: str = ""):
        """Update the status text while overlay is visible."""
        self._label.setText(text)
        self._sub_label.setText(sub_text)
        self.repaint()

    def hide(self):
        """Hide the overlay and stop the pulse animation."""
        self._dot.stop_animation()
        super().hide()

    def resizeEvent(self, event):
        self._sync_geometry()
        super().resizeEvent(event)

    def _sync_geometry(self):
        """Resize overlay to match parent bounds."""
        if self.parent():
            self.setGeometry(self.parent().rect())
