"""Central theme configuration for PDF_GUI.

Single source of truth for all colors, typography, and QSS generation.
No other module should contain hardcoded color values.

Design: "Silicon Terminal" — a dark, precision-oriented monitoring dashboard
grounded in the VLSI physical design subject matter.
"""

from dataclasses import dataclass

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPalette

from pdf_gui.models.config import FlowConfig, StatusColors


# ── Theme color tokens ──────────────────────────────────────────────

@dataclass(frozen=True)
class ThemeColors:
    """Neutral palette tokens for the Silicon Terminal dark theme.

    Status colors (SUCCESS/FAIL/RUNNING/PENDING) are NOT stored here —
    they come from FlowConfig.colors and are functional, not decorative.
    """
    bg_deep: str = "#0D1117"
    bg_surface: str = "#161B22"
    bg_header: str = "#21262D"
    border_subtle: str = "#30363D"
    text_primary: str = "#E6EDF3"
    text_secondary: str = "#8B949E"
    text_dim: str = "#484F58"

    # Dark-appropriate header variants for version_panel status bars.
    # These are the standard status colors adjusted to sit comfortably
    # on a dark background without overwhelming brightness.
    header_success: str = "#2D6A37"
    header_running: str = "#1A5A92"
    header_fail: str = "#7A1C1C"
    header_pending: str = "#7A4C00"


# ── QPalette builder ────────────────────────────────────────────────

def build_dark_palette(colors: ThemeColors) -> QPalette:
    """Return a QPalette configured for the Silicon Terminal dark theme."""
    p = QPalette()

    # Window
    p.setColor(QPalette.Window, QColor(colors.bg_deep))
    p.setColor(QPalette.WindowText, QColor(colors.text_primary))

    # Base (text fields, table cells)
    p.setColor(QPalette.Base, QColor(colors.bg_surface))
    p.setColor(QPalette.AlternateBase, QColor(colors.bg_deep))
    p.setColor(QPalette.Text, QColor(colors.text_primary))

    # Button
    p.setColor(QPalette.Button, QColor(colors.bg_header))
    p.setColor(QPalette.ButtonText, QColor(colors.text_primary))

    # Highlight (selection)
    p.setColor(QPalette.Highlight, QColor(colors.border_subtle))
    p.setColor(QPalette.HighlightedText, QColor(colors.text_primary))

    # Disabled
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors.text_dim))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(colors.text_dim))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors.text_dim))

    return p


# ── Global QSS stylesheet ───────────────────────────────────────────

def build_global_qss(colors: ThemeColors) -> str:
    """Return a single QSS stylesheet for the entire application."""
    return f"""
    QMainWindow {{
        background-color: {colors.bg_deep};
    }}
    QToolBar {{
        background-color: {colors.bg_header};
        border-bottom: 1px solid {colors.border_subtle};
        padding: 2px;
        spacing: 4px;
    }}
    QStatusBar {{
        background-color: {colors.bg_header};
        color: {colors.text_primary};
        border-top: 1px solid {colors.border_subtle};
    }}
    QTabWidget::pane {{
        border: 1px solid {colors.border_subtle};
        background-color: {colors.bg_deep};
    }}
    QTabBar::tab {{
        background-color: {colors.bg_surface};
        color: {colors.text_secondary};
        padding: 4px 14px;
        border: 1px solid {colors.border_subtle};
        border-bottom: none;
    }}
    QTabBar::tab:selected {{
        background-color: {colors.bg_header};
        color: {colors.text_primary};
    }}
    QTabBar::tab:hover {{
        background-color: {colors.border_subtle};
    }}
    QHeaderView::section {{
        background-color: {colors.bg_header};
        color: {colors.text_primary};
        font-weight: bold;
        border: 1px solid {colors.border_subtle};
        padding: 4px 6px;
    }}
    QTableWidget {{
        background-color: {colors.bg_deep};
        color: {colors.text_primary};
        gridline-color: {colors.border_subtle};
        border: none;
        alternate-background-color: {colors.bg_surface};
    }}
    QListWidget {{
        background-color: {colors.bg_surface};
        color: {colors.text_primary};
        border: none;
        outline: none;
    }}
    QListWidget::item {{
        border-bottom: 1px solid {colors.border_subtle};
        padding: 2px 4px;
    }}
    QListWidget::item:hover {{
        background-color: {colors.bg_header};
    }}
    QScrollArea {{
        background-color: {colors.bg_deep};
        border: none;
    }}
    QPushButton {{
        background-color: {colors.bg_header};
        color: {colors.text_primary};
        border: 1px solid {colors.border_subtle};
        padding: 4px 10px;
        border-radius: 2px;
    }}
    QPushButton:hover {{
        background-color: {colors.border_subtle};
    }}
    QPushButton:pressed {{
        background-color: {colors.bg_deep};
    }}
    QPushButton:disabled {{
        color: {colors.text_dim};
    }}
    QComboBox {{
        background-color: {colors.bg_header};
        color: {colors.text_primary};
        border: 1px solid {colors.border_subtle};
        padding: 2px 6px;
    }}
    QComboBox::drop-down {{
        border-left: 1px solid {colors.border_subtle};
    }}
    QComboBox QAbstractItemView {{
        background-color: {colors.bg_surface};
        color: {colors.text_primary};
        selection-background-color: {colors.bg_header};
    }}
    QLineEdit {{
        background-color: {colors.bg_surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border_subtle};
        padding: 2px 4px;
    }}
    QSpinBox {{
        background-color: {colors.bg_surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border_subtle};
        padding: 2px 4px;
    }}
    QDialog {{
        background-color: {colors.bg_deep};
        color: {colors.text_primary};
    }}
    QLabel {{
        color: {colors.text_primary};
    }}
    QRadioButton {{
        color: {colors.text_primary};
    }}
    QCheckBox {{
        color: {colors.text_primary};
    }}
    QMenu {{
        background-color: {colors.bg_surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border_subtle};
    }}
    QMenu::item:selected {{
        background-color: {colors.bg_header};
    }}
    QMenu::item:disabled {{
        color: {colors.text_dim};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {colors.border_subtle};
        margin: 4px 8px;
    }}
    """


# ── Status color helper ─────────────────────────────────────────────

# Dark-appropriate header color variants keyed by standard status color hex.
_HEADER_VARIANT_MAP = {
    "#4CAF50": ThemeColors.header_success,
    "#F44336": ThemeColors.header_fail,
    "#2196F3": ThemeColors.header_running,
    "#FF9800": ThemeColors.header_pending,
    # Also cover the old PENDING fallback
    "#9E9E9E": "#757575",
}


def status_color(config_colors: StatusColors, status_value) -> str:
    """Map any status enum (OverallStatus or StepStatus) to its hex color.

    Uses config-driven StatusColors. Returns the appropriate color for the
    given status value's .name attribute (e.g. 'SUCCESS', 'FAIL').

    Args:
        config_colors: StatusColors from FlowConfig.
        status_value: An enum with .name or .value attribute, e.g.
                      OverallStatus.SUCCESS or StepStatus.RUNNING.
    Returns:
        Hex color string, e.g. "#4CAF50".
    """
    name = getattr(status_value, "name", None) or str(status_value)
    return getattr(config_colors, name, "#9E9E9E")


def header_color(config_colors: StatusColors, status_value) -> str:
    """Return a dark-appropriate header bar color for the given status.

    Uses darker variants of the standard status colors so the header
    bar sits comfortably on a dark background.
    """
    standard = status_color(config_colors, status_value)
    return _HEADER_VARIANT_MAP.get(standard, "#757575")


# ── Theme application ───────────────────────────────────────────────

def apply_theme(app, config: FlowConfig):
    """Apply the complete Silicon Terminal theme in one call.

    Sets the QPalette, global QSS stylesheet, and fonts for the
    entire QApplication. Call once during startup and again after
    any UI rebuild that recreates widgets.
    """
    colors = ThemeColors()

    # Palette
    palette = build_dark_palette(colors)
    app.setPalette(palette)

    # Global QSS
    qss = build_global_qss(colors)
    app.setStyleSheet(qss)

    # Fonts: UI chrome gets the ui_font, data cells get data_font.
    # The global font is the UI font. Data cells override explicitly.
    ui_family = getattr(config, "ui_font", config.default_font)
    ui_size = config.default_font_size
    font = QFont(ui_family, ui_size)
    app.setFont(font)
