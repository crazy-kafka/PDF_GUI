import os
import subprocess

from PyQt5.QtCore import QSettings, Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QScrollArea,
                             QSplitter, QVBoxLayout, QWidget)

from pdf_gui.models.config import FlowConfig, load_config
from pdf_gui.models.run_data import Version
from pdf_gui.services.data_loader import load_versions
from pdf_gui.services.file_scanner import scan_runs
from pdf_gui.widgets.settings_dialog import SettingsDialog
from pdf_gui.widgets.sidebar import Sidebar
from pdf_gui.widgets.status_bar import StatusBar as SBWrapper
from pdf_gui.widgets.toolbar import ToolbarWidget
from pdf_gui.widgets.version_panel import VersionPanel


class MainWindow(QMainWindow):
    def __init__(self, config_path: str, runs_dir: str):
        super().__init__()
        self._config_path = config_path
        self._runs_dir = runs_dir
        self._config_mtime = 0
        self._fold_states: dict[str, bool] = {}

        self._config = self._reload_config()
        self._init_ui()
        self.refresh()

    def _reload_config(self) -> FlowConfig:
        try:
            mtime = os.path.getmtime(self._config_path)
            if mtime != self._config_mtime:
                self._config_mtime = mtime
                return load_config(self._config_path)
        except OSError:
            pass
        return getattr(self, "_config", load_config(self._config_path))

    def _init_ui(self):
        self.setWindowTitle(f"PDF GUI — {self._config.flow_name}")
        self.setMinimumSize(900, 500)
        self.resize(1100, 700)

        self._toolbar = ToolbarWidget(
            default_font=self._config.default_font,
            default_font_size=self._config.default_font_size,
        )
        self._toolbar.refresh_clicked.connect(self.refresh)
        self._toolbar.font_changed.connect(self._apply_font)
        self._toolbar.settings_clicked.connect(self._open_settings)
        self.addToolBar(self._toolbar)

        self._sidebar = Sidebar(self._config)
        self._sidebar.version_selected.connect(self._scroll_to_version)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_container = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_container)
        self._scroll_layout.setContentsMargins(4, 4, 4, 4)
        self._scroll_layout.addStretch()
        self._scroll_area.setWidget(self._scroll_container)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._scroll_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([230, 870])
        self.setCentralWidget(splitter)

        self._sb_wrapper = SBWrapper(self.statusBar())

        self._apply_font(self._config.default_font, self._config.default_font_size)

        if self._config.auto_refresh_seconds > 0:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.refresh)
            self._timer.start(self._config.auto_refresh_seconds * 1000)
        else:
            self._timer = None

    def refresh(self):
        cmd = self._get_refresh_command()
        if cmd:
            self._sb_wrapper.update_text("Running refresh script...")
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=300, cwd=self._runs_dir)
                if result.returncode != 0:
                    err = result.stderr.strip() or result.stdout.strip()
                    self._sb_wrapper.update_text(
                        f"Script failed (exit {result.returncode}): {err[:200]}")
            except subprocess.TimeoutExpired:
                self._sb_wrapper.update_text("Refresh script timed out")
            except Exception as e:
                self._sb_wrapper.update_text(f"Script error: {e}")

        self._config = self._reload_config()
        run_dirs = scan_runs(self._runs_dir)
        versions = load_versions(run_dirs, self._config)

        self.setUpdatesEnabled(False)

        # Save fold states for existing panels
        for i in range(self._scroll_layout.count()):
            w = self._scroll_layout.itemAt(i).widget()
            if isinstance(w, VersionPanel):
                self._fold_states[w.version_name()] = w.is_collapsed()

        # Remove existing panels (but not the stretch at the end)
        while self._scroll_layout.count() > 1:
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._panels: list[VersionPanel] = []
        for v in versions:
            panel = VersionPanel(v, self._config)
            if v.name in self._fold_states:
                panel.set_collapsed(self._fold_states[v.name])
            self._panels.append(panel)
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, panel)

        self._sidebar.rebuild(versions)

        self._sb_wrapper.update(
            len(versions),
            versions[0].name if versions else "",
        )

        self.setUpdatesEnabled(True)

    def _get_refresh_command(self) -> str:
        settings = QSettings("pdf_gui", "settings")
        gui_cmd = settings.value("refresh_command", "")
        if gui_cmd:
            return gui_cmd
        return self._config.refresh_command

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _scroll_to_version(self, name: str):
        for panel in self._panels:
            if panel.version_name() == name:
                self._scroll_area.ensureWidgetVisible(panel, 0, 20)
                break

    def _apply_font(self, family: str, size: int):
        font = QFont(family, size)
        QApplication.setFont(font)
