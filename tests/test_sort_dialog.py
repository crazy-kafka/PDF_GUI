from PyQt5.QtWidgets import QApplication

from pdf_gui.models.config import FlowConfig, MetricConfig, StepConfig
from pdf_gui.models.run_data import (OverallStatus, Step, StepStatus,
                                     Version)
from pdf_gui.widgets.sort_dialog import (SortDialog,
                                         apply_sort,
                                         MISSING_PUSH_BOTTOM,
                                         MISSING_PUSH_TOP,
                                         MISSING_EXCLUDE)


def make_config():
    return FlowConfig(
        steps=[
            StepConfig(name="init"),
            StepConfig(name="place"),
            StepConfig(name="route"),
        ],
        metrics=[
            MetricConfig(key="WNS"),
            MetricConfig(key="TNS"),
        ],
    )


def make_version(name: str, init_wns=None, init_tns=None):
    steps = []
    for sc in make_config().steps:
        metrics = {}
        if sc.name == "init":
            metrics = {"WNS": init_wns, "TNS": init_tns}
        elif sc.name == "place" and init_wns is not None:
            metrics = {"WNS": init_wns + 0.01 if init_wns else None,
                       "TNS": init_tns + 1.0 if init_tns else None}
        s = Step(name=sc.name, status=StepStatus.SUCCESS, metrics=metrics)
        steps.append(s)
    return Version(name=name, dir_path="/tmp", status=OverallStatus.SUCCESS,
                   steps=steps, latest_step="route")


def test_sort_dialog_default_date():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    config = make_config()
    dialog = SortDialog(config, {"rule": "date"})
    assert dialog._date_radio.isChecked()
    assert not dialog._metric_widget.isEnabled()


def test_metric_sort_descending():
    versions = [
        make_version("v1", init_wns=-0.500, init_tns=-20.0),
        make_version("v2", init_wns=-0.050, init_tns=-3.0),
        make_version("v3", init_wns=-0.100, init_tns=-8.0),
    ]
    config = {"rule": "metric", "step_name": "init", "metric_key": "WNS",
              "ascending": False, "missing": MISSING_PUSH_BOTTOM}
    result = apply_sort(versions, config)
    # descending: largest WNS first → -0.050, -0.100, -0.500
    assert result[0].name == "v2"  # -0.050
    assert result[1].name == "v3"  # -0.100
    assert result[2].name == "v1"  # -0.500


def test_metric_sort_ascending():
    versions = [
        make_version("v1", init_wns=-0.500),
        make_version("v2", init_wns=-0.050),
        make_version("v3", init_wns=-0.100),
    ]
    config = {"rule": "metric", "step_name": "init", "metric_key": "WNS",
              "ascending": True, "missing": MISSING_PUSH_BOTTOM}
    result = apply_sort(versions, config)
    # ascending: smallest WNS first → -0.500, -0.100, -0.050
    assert result[0].name == "v1"
    assert result[1].name == "v3"
    assert result[2].name == "v2"


def test_metric_sort_missing_push_bottom():
    # v3 has no "init" step — only 2 steps
    v3 = Version(name="v3", dir_path="/tmp", status=OverallStatus.SUCCESS,
                 steps=[
                     Step(name="place", status=StepStatus.SUCCESS,
                          metrics={"WNS": -0.100}),
                 ], latest_step="place")
    versions = [
        make_version("v1", init_wns=-0.500),
        v3,
        make_version("v2", init_wns=-0.050),
    ]
    config = {"rule": "metric", "step_name": "init", "metric_key": "WNS",
              "ascending": True, "missing": MISSING_PUSH_BOTTOM}
    result = apply_sort(versions, config)
    assert result[0].name == "v1"   # -0.500
    assert result[1].name == "v2"   # -0.050
    assert result[2].name == "v3"   # missing → bottom


def test_metric_sort_missing_exclude():
    v3 = Version(name="v3", dir_path="/tmp", status=OverallStatus.SUCCESS,
                 steps=[
                     Step(name="place", status=StepStatus.SUCCESS,
                          metrics={"WNS": -0.100}),
                 ], latest_step="place")
    versions = [
        make_version("v1", init_wns=-0.500),
        v3,
        make_version("v2", init_wns=-0.050),
    ]
    config = {"rule": "metric", "step_name": "init", "metric_key": "WNS",
              "ascending": True, "missing": MISSING_EXCLUDE}
    result = apply_sort(versions, config)
    assert len(result) == 2
    assert result[0].name == "v1"
    assert result[1].name == "v2"


def test_date_sort_preserves_scanner_order():
    versions = [
        make_version("v3"),
        make_version("v1"),
        make_version("v2"),
    ]
    result = apply_sort(versions, {"rule": "date"})
    assert [v.name for v in result] == ["v3", "v1", "v2"]
