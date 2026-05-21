"""Sort configuration dialog — choose date order or metric-based sort."""

import math
from typing import Callable, List, Optional

from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLabel, QPushButton, QRadioButton, QVBoxLayout,
                             QWidget)

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import Version

MISSING_PUSH_BOTTOM = "Push to bottom"
MISSING_PUSH_TOP = "Push to top"
MISSING_EXCLUDE = "Exclude"


class SortDialog(QDialog):
    def __init__(self, config: FlowConfig, current_rule: dict,
                 parent=None):
        super().__init__(parent)
        self._config = config
        self._current = current_rule
        self.setWindowTitle("Sort Versions")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # radio buttons
        self._date_radio = QRadioButton("Date (newest first)")
        self._metric_radio = QRadioButton("Metric value")
        self._metric_radio.toggled.connect(self._on_radio_toggled)
        layout.addWidget(self._date_radio)
        layout.addWidget(self._metric_radio)

        # metric controls
        self._metric_widget = QWidget()
        metric_layout = QVBoxLayout(self._metric_widget)
        metric_layout.setContentsMargins(20, 4, 0, 4)

        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step:"))
        self._step_combo = QComboBox()
        for sc in config.steps:
            self._step_combo.addItem(sc.label, sc.name)
        step_layout.addWidget(self._step_combo)
        step_layout.addStretch()
        metric_layout.addLayout(step_layout)

        met_layout = QHBoxLayout()
        met_layout.addWidget(QLabel("Metric:"))
        self._metric_combo = QComboBox()
        for mc in config.metrics:
            self._metric_combo.addItem(mc.label, mc.key)
        met_layout.addWidget(self._metric_combo)
        met_layout.addStretch()
        metric_layout.addLayout(met_layout)

        order_layout = QHBoxLayout()
        order_layout.addWidget(QLabel("Order:"))
        self._order_combo = QComboBox()
        self._order_combo.addItems(["Descending", "Ascending"])
        order_layout.addWidget(self._order_combo)
        order_layout.addStretch()
        metric_layout.addLayout(order_layout)

        layout.addWidget(self._metric_widget)

        # missing data
        miss_layout = QHBoxLayout()
        miss_layout.addWidget(QLabel("Missing data:"))
        self._missing_combo = QComboBox()
        self._missing_combo.addItems(
            [MISSING_PUSH_BOTTOM, MISSING_PUSH_TOP, MISSING_EXCLUDE])
        miss_layout.addWidget(self._missing_combo)
        miss_layout.addStretch()
        layout.addLayout(miss_layout)

        # buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply)
        buttons.addButton(apply_btn, QDialogButtonBox.AcceptRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # restore current state
        self._restore()
        self._on_radio_toggled()

    def _restore(self):
        if self._current.get("rule") == "metric":
            self._metric_radio.setChecked(True)
            step_name = self._current.get("step_name", "")
            metric_key = self._current.get("metric_key", "")
            idx = self._step_combo.findData(step_name)
            if idx >= 0:
                self._step_combo.setCurrentIndex(idx)
            idx = self._metric_combo.findData(metric_key)
            if idx >= 0:
                self._metric_combo.setCurrentIndex(idx)
            if self._current.get("ascending", False):
                self._order_combo.setCurrentText("Ascending")
            self._missing_combo.setCurrentText(
                self._current.get("missing", MISSING_PUSH_BOTTOM))
        else:
            self._date_radio.setChecked(True)

    def _on_radio_toggled(self):
        self._metric_widget.setEnabled(self._metric_radio.isChecked())

    def _apply(self):
        self._result = {"rule": "date"}
        if self._metric_radio.isChecked():
            self._result = {
                "rule": "metric",
                "step_name": self._step_combo.currentData(),
                "metric_key": self._metric_combo.currentData(),
                "ascending": self._order_combo.currentText() == "Ascending",
                "missing": self._missing_combo.currentText(),
            }
        self.accept()

    def result(self) -> dict:
        return getattr(self, "_result", self._current)


def apply_sort(versions: List[Version], sort_config: dict) -> List[Version]:
    """Return sorted list of versions. Date sort keeps scanner order."""
    if sort_config.get("rule") != "metric":
        return list(versions)  # date order — already sorted by scanner

    step_name = sort_config["step_name"]
    metric_key = sort_config["metric_key"]
    ascending = sort_config.get("ascending", False)
    missing = sort_config.get("missing", MISSING_PUSH_BOTTOM)

    def _key(v: Version):
        for s in v.steps:
            if s.name == step_name:
                val = s.metrics.get(metric_key)
                if val is not None:
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
                break
        # missing
        if missing == MISSING_PUSH_BOTTOM:
            return math.inf if ascending else -math.inf
        elif missing == MISSING_PUSH_TOP:
            return -math.inf if ascending else math.inf
        else:
            return None

    result = [v for v in versions
              if not (missing == MISSING_EXCLUDE and _key(v) is None)]
    result.sort(key=_key, reverse=not ascending)
    return result
