"""Chart configuration dialog — select type, step, metrics, versions."""

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLabel, QListWidget, QListWidgetItem, QMessageBox,
                             QPushButton, QRadioButton, QVBoxLayout, QWidget)

from pdf_gui.models.config import FlowConfig

STATUS_COLORS = {
    "SUCCESS": "#4CAF50", "RUNNING": "#2196F3",
    "FAIL": "#F44336", "PENDING": "#FF9800",
}

CHART_TYPES = ["Line/Bar", "Scatter", "Histogram"]


class ChartDialog(QDialog):
    def __init__(self, df: pd.DataFrame, config: FlowConfig, parent=None):
        super().__init__(parent)
        self._df = df
        self._config = config
        self._all_versions = sorted(df["version_name"].unique().tolist())
        self.setWindowTitle("Chart Versions")
        self.setMinimumSize(420, 450)

        layout = QVBoxLayout(self)

        # chart type radios
        layout.addWidget(QLabel("Chart type:"))
        self._type_radios = []
        type_layout = QHBoxLayout()
        for ct in CHART_TYPES:
            rb = QRadioButton(ct)
            rb.toggled.connect(self._on_type_changed)
            self._type_radios.append(rb)
            type_layout.addWidget(rb)
        self._type_radios[0].setChecked(True)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # group filter
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Group:"))
        self._group_combo = QComboBox()
        for g in config.step_groups:
            self._group_combo.addItem(g.label or g.name, g.name)
        self._group_combo.currentIndexChanged.connect(self._on_group_changed)
        group_layout.addWidget(self._group_combo)
        group_layout.addStretch()
        layout.addLayout(group_layout)

        # step
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step:"))
        self._step_combo = QComboBox()
        step_layout.addWidget(self._step_combo)
        step_layout.addStretch()
        layout.addLayout(step_layout)

        # Y metric
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Metric (Y):"))
        self._y_combo = QComboBox()
        y_layout.addWidget(self._y_combo)
        y_layout.addStretch()
        layout.addLayout(y_layout)

        # X metric (scatter only)
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("Metric (X):"))
        self._x_combo = QComboBox()
        self._x_combo.setEnabled(False)
        x_layout.addWidget(self._x_combo)
        x_layout.addStretch()
        layout.addLayout(x_layout)

        # version list
        layout.addWidget(QLabel("Versions:"))
        self._list = QListWidget()
        layout.addWidget(self._list)

        sel_layout = QHBoxLayout()
        all_btn = QPushButton("Select All")
        all_btn.clicked.connect(lambda: self._set_all(Qt.Checked))
        sel_layout.addWidget(all_btn)
        none_btn = QPushButton("Deselect All")
        none_btn.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        sel_layout.addWidget(none_btn)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        # buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        plot_btn = QPushButton("Plot")
        plot_btn.clicked.connect(self._plot)
        buttons.addButton(plot_btn, QDialogButtonBox.AcceptRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_group_changed()  # populate step/metric/version for first group

    def _populate_step_metric(self, group_name):
        self._step_combo.clear()
        self._y_combo.clear()
        self._x_combo.clear()
        seen_s, seen_m = set(), set()
        for g in self._config.step_groups:
            if group_name and g.name != group_name:
                continue
            for sn in [s.name for s in g.steps]:
                if sn not in seen_s:
                    seen_s.add(sn)
                    self._step_combo.addItem(sn, sn)
            for m in g.metrics:
                if m.key not in seen_m:
                    seen_m.add(m.key)
                    self._y_combo.addItem(m.key, m.key)
                    self._x_combo.addItem(m.key, m.key)

    def _on_group_changed(self):
        group_name = self._group_combo.currentData()
        self._populate_step_metric(group_name)
        self._rebuild_version_list(group_name)

    def _rebuild_version_list(self, group_name):
        self._list.clear()
        for g in self._config.step_groups:
            if group_name and g.name != group_name:
                continue
            group_steps = set(s.name for s in g.steps)
            for vname in self._all_versions:
                vstatus = self._df[self._df["version_name"] == vname][
                    "version_status"].iloc[0]
                # check if this version has steps in group
                v_steps = set(self._df[
                    (self._df["version_name"] == vname) &
                    (self._df["step_name"].isin(group_steps))
                ]["step_name"].unique())
                if not v_steps:
                    continue
                item = QListWidgetItem(f"{vname} ({vstatus})")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, vname)
                self._list.addItem(item)

    def _set_all(self, state):
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(state)

    def _on_type_changed(self):
        if not hasattr(self, "_x_combo"):
            return  # __init__ not complete yet
        is_scatter = any(
            rb.isChecked() and rb.text() == "Scatter"
            for rb in self._type_radios)
        self._x_combo.setEnabled(is_scatter)

    def _plot(self):
        chart_type = next(
            rb.text() for rb in self._type_radios if rb.isChecked())
        step_name = self._step_combo.currentData()
        y_metric = self._y_combo.currentData()
        x_metric = self._x_combo.currentData() if chart_type == "Scatter" else None

        selected = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))

        if not selected:
            QMessageBox.warning(self, "Chart", "No versions selected.")
            return

        # filter DataFrame
        mask = (self._df["step_name"] == step_name) & \
               self._df["version_name"].isin(selected)
        chart_df = self._df[mask].dropna(subset=[y_metric])
        if chart_type == "Scatter":
            chart_df = chart_df.dropna(subset=[x_metric])

        if chart_df.empty:
            QMessageBox.warning(
                self, "Chart",
                f"No data for {y_metric} at step '{step_name}'.")
            return

        if chart_type == "Scatter" and len(chart_df) < 2:
            QMessageBox.warning(
                self, "Chart",
                "Need at least 2 data points for scatter plot.")
            return

        self._result = {
            "chart_type": chart_type,
            "step_name": step_name,
            "y_metric": y_metric,
            "x_metric": x_metric,
            "chart_df": chart_df,
            "title": f"{y_metric} at {step_name}",
        }
        self.accept()

    def result(self):
        return getattr(self, "_result", None)
