import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from pdf_gui.models.config import (FlowConfig, MetricConfig, StepConfig,
                                   StepGroupConfig)
from pdf_gui.widgets.chart_dialog import ChartDialog


def make_config():
    return FlowConfig(
        steps=[StepConfig(name="init"), StepConfig(name="place")],
        metrics=[MetricConfig(key="WNS"), MetricConfig(key="TNS")],
    )


def make_df():
    return pd.DataFrame({
        "version_name": ["v1", "v1", "v2", "v2"],
        "version_status": ["SUCCESS", "SUCCESS", "FAIL", "FAIL"],
        "step_name": ["init", "place", "init", "place"],
        "step_status": ["SUCCESS", "SUCCESS", "SUCCESS", "FAIL"],
        "WNS": [-0.050, -0.100, -0.500, None],
        "TNS": [-3.0, -5.0, -20.0, None],
        "job_status": ["SUCCESS"] * 4,
        "job_runtime": ["5m", "30m", "8m", "60m"],
        "job_memory_current_mb": [4096.0] * 4,
        "job_cpu_current_pct": [75.0] * 4,
    })


def test_chart_dialog_defaults():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    dialog = ChartDialog(make_df(), make_config())
    # first chart type radio checked
    assert dialog._type_radios[0].isChecked()
    # X metric disabled (not scatter)
    assert not dialog._x_combo.isEnabled()
    # all versions checked
    for i in range(dialog._list.count()):
        assert dialog._list.item(i).checkState() == Qt.Checked


def test_chart_dialog_scatter_enables_x_metric():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    dialog = ChartDialog(make_df(), make_config())
    assert not dialog._x_combo.isEnabled()
    # click Scatter radio
    for rb in dialog._type_radios:
        if rb.text() == "Scatter":
            rb.setChecked(True)
            break
    assert dialog._x_combo.isEnabled()


def test_chart_version_filter_by_group():
    """Version list filters to only versions with steps in selected group."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    df = pd.DataFrame({
        "version_name": ["v1", "v1", "v2"],
        "version_status": ["SUCCESS", "SUCCESS", "RUNNING"],
        "step_name": ["init", "sta", "init"],
        "step_status": ["SUCCESS", "SUCCESS", "RUNNING"],
        "WNS": [-0.050, -0.030, -0.100],
        "TNS": [-3.0, -2.0, -5.0],
        "job_status": ["SUCCESS"] * 3,
        "job_runtime": ["5m"] * 3,
        "job_memory_current_mb": [4096.0] * 3,
        "job_cpu_current_pct": [75.0] * 3,
    })
    from pdf_gui.models.config import StepGroupConfig, MetricConfig
    config = FlowConfig(
        step_groups=[
            StepGroupConfig(name="APR", steps=["init"],
                            metrics=[MetricConfig(key="WNS")]),
            StepGroupConfig(name="STA", steps=["sta"],
                            metrics=[MetricConfig(key="WNS")]),
        ],
    )
    dialog = ChartDialog(df, config)

    # Default group is APR → only v1 and v2 have "init"
    names = [dialog._list.item(i).data(Qt.UserRole)
             for i in range(dialog._list.count())
             if dialog._list.item(i).checkState() == Qt.Checked]
    assert "v1" in names
    assert "v2" in names

    # Switch to STA → only v1 has "sta"
    dialog._group_combo.setCurrentIndex(1)  # STA
    names_sta = [dialog._list.item(i).data(Qt.UserRole)
                 for i in range(dialog._list.count())
                 if dialog._list.item(i).checkState() == Qt.Checked]
    assert "v1" in names_sta
    assert "v2" not in names_sta
