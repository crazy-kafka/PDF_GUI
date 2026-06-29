import os
import subprocess

from PyQt5.QtCore import QSettings, Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QScrollArea,
                             QSplitter, QTabWidget, QVBoxLayout, QWidget)

from pdf_gui.models.config import FlowConfig, load_config, validate_config
from pdf_gui.models.run_data import GroupedVersion, Version, make_grouped_versions
from pdf_gui.services.data_loader import derive_overall, load_versions
from pdf_gui.services.file_scanner import scan_runs
from pdf_gui.utils.log import get_logger
from pdf_gui.widgets.export_dialog import ExportDialog
from pdf_gui.services.dataframe_builder import build_dataframe
from pdf_gui.services.data_loader import derive_overall
from pdf_gui.widgets.chart_dialog import ChartDialog
from pdf_gui.widgets.chart_window import ChartWindow
from pdf_gui.widgets.settings_dialog import SettingsDialog
from pdf_gui.widgets.sort_dialog import SortDialog, apply_sort
from pdf_gui.widgets.sidebar import Sidebar
from pdf_gui.widgets.status_bar import StatusBar as SBWrapper
from pdf_gui.widgets.toolbar import ToolbarWidget
from pdf_gui.widgets.version_panel import VersionPanel
from pdf_gui import theme

log = get_logger()


class MainWindow(QMainWindow):
    def __init__(self, config_path: str, runs_dir: str,
                 cli_refresh_command: str = None):
        super().__init__()
        self._config_path = config_path
        self._runs_dir = runs_dir
        self._cli_refresh_command = cli_refresh_command
        self._config_mtime = 0
        self._fold_states: dict[str, bool] = {}
        self._sort_config: dict = {"rule": "date"}
        self._panels: list[VersionPanel] = []
        self._dataframe = None
        self._raw_versions: list = []

        self._config = self._reload_config()
        validate_config(self._config)
        self._init_ui()
        self.refresh()

    def _reload_config(self) -> FlowConfig:
        try:
            mtime = os.path.getmtime(self._config_path)
            if mtime != self._config_mtime:
                self._config_mtime = mtime
                return load_config(self._config_path)
        except OSError as e:
            log.warning("Could not check config mtime: %s", e)
        return getattr(self, "_config", load_config(self._config_path))

    def _init_ui(self):
        self.setWindowTitle(f"PDF GUI — {self._config.flow_name}")
        self.setMinimumSize(900, 500)
        self.resize(1100, 700)

        self._toolbar = ToolbarWidget(
            default_font=self._config.ui_font,
            default_font_size=self._config.default_font_size,
            data_font=self._config.data_font,
        )
        self._toolbar.refresh_clicked.connect(self.refresh)
        self._toolbar.font_changed.connect(self._apply_font)
        self._toolbar.settings_clicked.connect(self._open_settings)
        self._toolbar.export_clicked.connect(self._open_export)
        self._toolbar.sort_clicked.connect(self._open_sort)
        self._toolbar.chart_clicked.connect(self._open_chart)
        self.addToolBar(self._toolbar)

        self._sidebar = Sidebar(self._config)
        self._sidebar.version_selected.connect(self._scroll_to_version)

        self._group_scrolls = []  # [(group_name, QScrollArea, QVBoxLayout)]
        self._active_group_index = 0

        if self._config.step_groups:
            self._tab_widget = QTabWidget()
            for g in self._config.step_groups:
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                container = QWidget()
                layout = QVBoxLayout(container)
                layout.setContentsMargins(4, 4, 4, 4)
                layout.addStretch()
                scroll.setWidget(container)
                self._tab_widget.addTab(scroll, g.label or g.name)
                self._group_scrolls.append((g, scroll, layout))
            self._tab_widget.currentChanged.connect(self._on_tab_changed)

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
        if self._config.step_groups:
            splitter.addWidget(self._tab_widget)
        else:
            splitter.addWidget(self._scroll_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([230, 870])
        self.setCentralWidget(splitter)

        self._sb_wrapper = SBWrapper(self.statusBar())

        self._apply_font(self._config.ui_font, self._config.default_font_size)

        theme.apply_theme(QApplication.instance(), self._config)

        if self._config.auto_refresh_seconds > 0:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.refresh)
            self._timer.start(self._config.auto_refresh_seconds * 1000)
        else:
            self._timer = None

    def refresh(self):
        log.info("Refresh started")
        cmd = self._get_refresh_command()
        if cmd:
            log.info("Running refresh script: %s", cmd)
            self._sb_wrapper.update_text("Running refresh script...")
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=300)
                if result.returncode != 0:
                    err = result.stderr.strip() or result.stdout.strip()
                    log.error("Refresh script failed (exit %d): %s",
                              result.returncode, err[:200])
                    self._sb_wrapper.update_text(
                        f"Script failed (exit {result.returncode}): {err[:200]}")
            except subprocess.TimeoutExpired:
                log.error("Refresh script timed out after 300s")
                self._sb_wrapper.update_text("Refresh script timed out")
            except Exception as e:
                log.error("Refresh script error: %s", e)
                self._sb_wrapper.update_text(f"Script error: {e}")

        self._config = self._reload_config()
        if self._config_mtime:
            log.info("Config reloaded (file changed)")
        run_dirs = scan_runs(self._runs_dir)
        versions = load_versions(run_dirs, self._config)
        versions = apply_sort(versions, self._sort_config)
        if self._sort_config.get("rule") == "metric":
            sc = self._sort_config
            log.info("Sorted by %s/%s (%s)",
                     sc["step_name"], sc["metric_key"],
                     "ascending" if sc.get("ascending") else "descending")

        self._dataframe = build_dataframe(versions, self._config)
        self._raw_versions = versions
        self._rebuild_ui(versions)
        log.info("Refresh complete: %d versions loaded", len(versions))

    def _rebuild_ui(self, versions):
        self.setUpdatesEnabled(False)

        if self._config.step_groups:
            self._rebuild_group_tabs(versions)
            idx = self._tab_widget.currentIndex()
            if 0 <= idx < len(self._group_scrolls):
                self._active_group_index = idx
        else:
            self._rebuild_single_scroll(versions)

        self._sb_wrapper.update(versions, self._sort_config)
        theme.apply_theme(QApplication.instance(), self._config)
        self.setUpdatesEnabled(True)

    def _rebuild_single_scroll(self, versions):
        versions = [v for v in versions if v.steps]
        for i in range(self._scroll_layout.count()):
            w = self._scroll_layout.itemAt(i).widget()
            if isinstance(w, VersionPanel):
                self._fold_states[w.version_name()] = w.is_collapsed()
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

    def _rebuild_group_tabs(self, versions):
        all_gv = []
        for g_idx, (group, scroll, layout) in enumerate(self._group_scrolls):
            gv_list = make_grouped_versions(versions, [s.name for s in group.steps], derive_overall)

            for i in range(layout.count()):
                w = layout.itemAt(i).widget()
                if isinstance(w, VersionPanel):
                    self._fold_states[w.version_name()] = w.is_collapsed()
            while layout.count() > 1:
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            panels = []
            for gv in gv_list:
                panel = VersionPanel(gv, self._config, group=group)
                if gv.name in self._fold_states:
                    panel.set_collapsed(self._fold_states[gv.name])
                panels.append(panel)
                layout.insertWidget(layout.count() - 1, panel)

            if g_idx == self._active_group_index:
                all_gv = gv_list
                self._sidebar.rebuild(gv_list)
        self._panels = [p for _, _, layout in self._group_scrolls
                        for i in range(layout.count())
                        if isinstance(layout.itemAt(i).widget(), VersionPanel)
                        and (p := layout.itemAt(i).widget())]

    def _on_tab_changed(self, idx):
        if 0 <= idx < len(self._group_scrolls):
            self._active_group_index = idx
            group, _, layout = self._group_scrolls[idx]
            gv_list = []
            for i in range(layout.count()):
                w = layout.itemAt(i).widget()
                if isinstance(w, VersionPanel):
                    gv_list.append(w._gv)
            self._sidebar.rebuild(gv_list)

    def _get_refresh_command(self) -> str:
        if self._cli_refresh_command is not None:
            return self._cli_refresh_command
        settings = QSettings("pdf_gui", "settings")
        gui_cmd = settings.value("refresh_command", "")
        if gui_cmd:
            return gui_cmd
        return self._config.refresh_command

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _open_export(self):
        versions = list(self._raw_versions) if self._raw_versions else []
        if not versions:
            return
        dialog = ExportDialog(versions, self._config, self)
        dialog.exec_()

    def _open_chart(self):
        if self._dataframe is None or self._dataframe.empty:
            return
        dialog = ChartDialog(self._dataframe, self._config, self)
        if dialog.exec_() == ChartDialog.Accepted:
            chart_config = dialog.result()
            if chart_config is None:
                return
            window = ChartWindow(chart_config, self)
            window.show()
            if not hasattr(self, "_chart_windows"):
                self._chart_windows = []
            self._chart_windows.append(window)

    def _open_sort(self):
        dialog = SortDialog(self._config, self._sort_config, self)
        if dialog.exec_() == SortDialog.Accepted:
            self._sort_config = dialog.result()
            versions = list(self._raw_versions)
            versions = apply_sort(versions, self._sort_config)
            if self._sort_config.get("rule") == "metric":
                sc = self._sort_config
                log.info("Sorted by %s/%s (%s)",
                         sc["step_name"], sc["metric_key"],
                         "ascending" if sc.get("ascending") else "descending")
            else:
                log.info("Sorted by date (newest first)")
            self._dataframe = build_dataframe(versions, self._config)
            self._raw_versions = versions
            self._rebuild_ui(versions)

    def _scroll_to_version(self, name: str):
        if self._config.step_groups:
            idx = self._tab_widget.currentIndex()
            if 0 <= idx < len(self._group_scrolls):
                _, scroll, layout = self._group_scrolls[idx]
                for i in range(layout.count()):
                    w = layout.itemAt(i).widget()
                    if isinstance(w, VersionPanel) and w.version_name() == name:
                        scroll.ensureWidgetVisible(w, 0, 20)
                        return
        else:
            for panel in self._panels:
                if panel.version_name() == name:
                    self._scroll_area.ensureWidgetVisible(panel, 0, 20)
                    break

    def _apply_font(self, family: str, size: int):
        font = QFont(family, size)
        QApplication.setFont(font)
        # Data font: same size, but keep the configured data font family
        self._data_font = QFont(self._config.data_font, size)
        if self._config.step_groups:
            for _, _, layout in self._group_scrolls:
                for i in range(layout.count()):
                    w = layout.itemAt(i).widget()
                    if isinstance(w, VersionPanel):
                        w.resize_for_font()
        else:
            for panel in self._panels:
                panel.resize_for_font()
