"""Central theme configuration for PDF_GUI.

Single source of truth for all colors, typography, and QSS generation.
No other module should contain hardcoded color values.

Designs:
- "Silicon Terminal" (dark) — a dark, precision-oriented monitoring
  dashboard grounded in the VLSI physical design subject matter.
- "Cleanroom" (light) — warm paper whites and amber undertones echoing
  semiconductor fab cleanroom lighting (photoresist-safe 589nm lamps).
"""

from dataclasses import dataclass

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

from pdf_gui.models.config import FlowConfig, StatusColors


# ── Theme color tokens ──────────────────────────────────────────────

@dataclass(frozen=True)
class ThemeColors:
    """Neutral palette tokens for a PDF_GUI color theme.

    Status colors (SUCCESS/FAIL/RUNNING/PENDING) are NOT stored here —
    they come from FlowConfig.colors and are functional, not decorative.

    Instances are immutable; see the module-level DARK / LIGHT presets.
    """
    bg_deep: str
    bg_surface: str
    bg_header: str
    border_subtle: str
    text_primary: str
    text_secondary: str
    text_dim: str

    # Header variants for version_panel status bars — the standard status
    # colors adjusted to sit comfortably on this theme's background.
    header_success: str
    header_running: str
    header_fail: str
    header_pending: str

    # Table header background — kept separate from bg_header (chrome) so
    # light mode can use a clean non-grey header.
    table_header_bg: str
    # Table alternate-row background. Light mode uses the same white as
    # the base cells for a clean, uniform look.
    table_alt_bg: str
    # Strong metric separators — distinct from the regular gridline while
    # remaining neutral enough to fit both themes.
    metric_separator: str
    # Text color on version_panel header bars (white on dark, dark on light).
    header_text: str


DARK = ThemeColors(
    bg_deep="#0D1117",
    bg_surface="#161B22",
    bg_header="#21262D",
    border_subtle="#30363D",
    text_primary="#E6EDF3",
    text_secondary="#8B949E",
    text_dim="#484F58",
    header_success="#2D6A37",
    header_running="#1A5A92",
    header_fail="#7A1C1C",
    header_pending="#7A4C00",
    table_header_bg="#21262D",
    table_alt_bg="#161B22",
    metric_separator="#58A6B8",
    header_text="#FFFFFF",
)

LIGHT = ThemeColors(
    bg_deep="#FBF8F4",
    bg_surface="#F0EDE6",
    bg_header="#E5E0D6",
    border_subtle="#C8C2B5",
    text_primary="#1E1B18",
    text_secondary="#6B6358",
    text_dim="#A0988A",
    header_success="#8CC99A",
    header_running="#7DB5E8",
    header_fail="#E8837D",
    header_pending="#EBC560",
    table_header_bg="#FBF8F4",
    table_alt_bg="#FBF8F4",
    metric_separator="#5F7F86",
    header_text="#1E1B18",
)

_THEMES = {
    "dark": DARK,
    "light": LIGHT,
}
_current_name = "dark"


def theme_names() -> list:
    """Return the available theme names (capitalized, e.g. 'Dark')."""
    return [n.capitalize() for n in _THEMES]


def set_theme(name: str) -> None:
    """Switch the active theme by name ('Dark' / 'Light')."""
    global _current_name
    key = name.strip().lower()
    if key not in _THEMES:
        raise ValueError(
            f"Unknown theme: {name!r}; available: {theme_names()}")
    _current_name = key


def get_theme() -> ThemeColors:
    """Return the currently active theme's color tokens."""
    return _THEMES[_current_name]


def get_theme_name() -> str:
    """Return the active theme's display name (e.g. 'Dark')."""
    return _current_name.capitalize()


# ── QPalette builder ────────────────────────────────────────────────

def build_palette(colors: ThemeColors) -> QPalette:
    """Return a QPalette configured from the given theme tokens."""
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
        background-color: {colors.table_header_bg};
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
        alternate-background-color: {colors.table_alt_bg};
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
    """Return a header bar color for the given status for the active theme.

    Uses theme-appropriate variants of the standard status colors so the
    header bar sits comfortably on the current background.
    """
    standard = status_color(config_colors, status_value)
    colors = get_theme()
    variants = {
        "#4CAF50": colors.header_success,
        "#F44336": colors.header_fail,
        "#2196F3": colors.header_running,
        "#FF9800": colors.header_pending,
        # Also cover the old PENDING fallback
        "#9E9E9E": colors.text_dim,
    }
    return variants.get(standard, colors.text_dim)


# ── Theme application ───────────────────────────────────────────────

def apply_theme(app, config: FlowConfig):
    """Apply the complete Silicon Terminal theme in one call.

    Sets the QPalette and global QSS stylesheet for the entire
    QApplication. Fonts are managed by MainWindow (so the user's
    toolbar font choice is not reset on rebuild). Call once during
    startup and again after any UI rebuild that recreates widgets.
    """
    colors = get_theme()

    # Palette
    palette = build_palette(colors)
    app.setPalette(palette)

    # Global QSS
    qss = build_global_qss(colors)
    app.setStyleSheet(qss)
