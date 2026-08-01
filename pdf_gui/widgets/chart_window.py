"""Matplotlib chart window for cross-version data visualization."""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg,
                                                NavigationToolbar2QT)
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from pdf_gui import theme


class ChartWindow(QMainWindow):
    def __init__(self, chart_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"PDF GUI — {chart_config['title']}")
        self.resize(800, 550)
        self._config = chart_config

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        fig, ax = plt.subplots(figsize=(8, 5))
        self._fig = fig
        self._ax = ax

        self._bars = None
        self._scatter = None
        self._draw(chart_config)

        canvas = FigureCanvasQTAgg(fig)
        layout.addWidget(canvas)

        toolbar = NavigationToolbar2QT(canvas, self)
        layout.addWidget(toolbar)

        self._fig.canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _draw(self, cfg):
        chart_type = cfg["chart_type"]
        df = cfg["chart_df"]
        y_metric = cfg["y_metric"]

        # Config-driven status colors
        status_colors_cfg = cfg.get("status_colors", {})
        colors = [status_colors_cfg.get(s, theme.get_theme().text_secondary)
                  for s in df["version_status"]]

        # Matplotlib styling following the active theme
        tc = theme.get_theme()
        self._fig.patch.set_facecolor(tc.bg_deep)
        self._ax.set_facecolor(tc.bg_surface)
        self._ax.tick_params(colors=tc.text_secondary)
        self._ax.xaxis.label.set_color(tc.text_primary)
        self._ax.yaxis.label.set_color(tc.text_primary)
        self._ax.title.set_color(tc.text_primary)
        for spine in self._ax.spines.values():
            spine.set_color(tc.border_subtle)

        if chart_type == "Line/Bar":
            names = df["version_name"].apply(
                lambda x: x[:20] + ".." if len(x) > 20 else x)
            self._bars = self._ax.bar(
                names, df[y_metric], color=colors,
                edgecolor=tc.bg_deep)
            self._ax.set_ylabel(y_metric)
            self._ax.set_title(cfg["title"])
            self._fig.autofmt_xdate(rotation=45, ha="right")
            self._ax.tick_params(axis="x", colors=tc.text_secondary)

        elif chart_type == "Scatter":
            x_metric = cfg["x_metric"]
            self._scatter = self._ax.scatter(
                df[x_metric], df[y_metric], c=colors,
                alpha=0.7, edgecolors=tc.bg_deep)
            self._ax.set_xlabel(x_metric)
            self._ax.set_ylabel(y_metric)
            self._ax.set_title(
                f"{x_metric} vs {y_metric} at {cfg['step_name']}")

        elif chart_type == "Histogram":
            hist_color = cfg.get("histogram_color", tc.bg_header)
            mean_color = status_colors_cfg.get("FAIL", "#F44336")
            median_color = status_colors_cfg.get("RUNNING", "#2196F3")
            self._ax.hist(df[y_metric], bins="auto",
                          edgecolor=tc.bg_deep,
                          alpha=0.7, color=hist_color)
            mean_val = df[y_metric].mean()
            median_val = df[y_metric].median()
            self._ax.axvline(mean_val, color=mean_color, linestyle="--",
                             linewidth=2, label=f"Mean: {mean_val:.3f}")
            self._ax.axvline(median_val, color=median_color, linestyle=":",
                             linewidth=2, label=f"Median: {median_val:.3f}")
            self._ax.set_xlabel(y_metric)
            self._ax.set_ylabel("Count")
            self._ax.set_title(cfg["title"])
            legend = self._ax.legend()
            for text in legend.get_texts():
                text.set_color(tc.text_primary)

        self._fig.tight_layout()

    def _on_hover(self, event):
        if event.inaxes != self._ax:
            self.statusBar().clearMessage()
            return

        chart_type = self._config["chart_type"]
        df = self._config["chart_df"]

        if chart_type == "Line/Bar" and self._bars is not None:
            for bar, vname in zip(self._bars, df["version_name"]):
                if bar.contains(event)[0]:
                    self.statusBar().showMessage(vname)
                    return

        elif chart_type == "Scatter" and self._scatter is not None:
            pts, indices = self._scatter.contains(event)
            if pts:
                idx = indices["ind"][0]
                self.statusBar().showMessage(df["version_name"].iloc[idx])
                return

        self.statusBar().clearMessage()

    def closeEvent(self, event):
        plt.close(self._fig)
        super().closeEvent(event)
