import json
import os
import tempfile

from pdf_gui.models.config import FlowConfig, MetricConfig, StepConfig
from pdf_gui.models.run_data import (Job, OverallStatus, Step, StepStatus,
                                     Version)
from pdf_gui.services.data_loader import load_versions
from pdf_gui.services.file_scanner import scan_runs


def make_config():
    return FlowConfig(
        flow_name="Test",
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


def make_run_dir(parent: str, dir_name: str, run_info: dict,
                 step_files: dict[str, dict]) -> str:
    """Create a run directory with run_info.json and step JSON files."""
    run_dir = os.path.join(parent, dir_name)
    os.makedirs(run_dir)
    with open(os.path.join(run_dir, "run_info.json"), "w") as f:
        json.dump(run_info, f)
    for step_name, data in step_files.items():
        with open(os.path.join(run_dir, f"{step_name}.json"), "w") as f:
            json.dump(data, f)
    return run_dir


def test_scan_runs():
    with tempfile.TemporaryDirectory() as tmp:
        runs = os.path.join(tmp, "runs")
        os.makedirs(runs)
        os.makedirs(os.path.join(runs, "2026-01-01_1200_golden"))
        os.makedirs(os.path.join(runs, "2026-01-02_1200_eco"))
        os.makedirs(os.path.join(runs, "not_a_run"))  # no timestamp prefix
        os.makedirs(os.path.join(runs, "2026-01-03_1200_latest"))
        # Create a file that's not a directory
        with open(os.path.join(runs, "2026-01-04_1200_file.txt"), "w") as f:
            f.write("not a dir")

        dirs = scan_runs(runs)
        assert len(dirs) == 3  # only timestamped dirs
        # Most recent first
        assert "2026-01-03" in os.path.basename(dirs[0])
        assert "2026-01-01" in os.path.basename(dirs[2])


def test_load_all_success():
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        make_run_dir(tmp, "2026-01-01_1200_chip_A", {"version": "chip_A"},
                     {
                         "init": {"step": "init", "status": "SUCCESS",
                                  "metrics": {"WNS": None, "TNS": None},
                                  "job": {"status": "SUCCESS", "runtime": "5m"}},
                         "place": {"step": "place", "status": "SUCCESS",
                                   "metrics": {"WNS": -0.100, "TNS": -3.0},
                                   "job": {"status": "SUCCESS", "runtime": "30m"}},
                         "route": {"step": "route", "status": "SUCCESS",
                                   "metrics": {"WNS": -0.050, "TNS": -1.2},
                                   "job": {"status": "SUCCESS", "runtime": "45m"}},
                     })
        versions = load_versions([os.path.join(tmp, d)
                                  for d in os.listdir(tmp)], config)
        assert len(versions) == 1
        v = versions[0]
        assert v.name == "chip_A"
        assert v.status == OverallStatus.SUCCESS
        assert v.latest_step == "route"
        assert len(v.steps) == 3
        assert v.steps[1].metrics["WNS"] == -0.100
        assert v.steps[0].metrics["WNS"] is None


def test_load_with_fail():
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        make_run_dir(tmp, "2026-01-01_1200_chip_B", {"version": "chip_B"},
                     {
                         "init": {"step": "init", "status": "SUCCESS",
                                  "metrics": {}, "job": {}},
                         "place": {"step": "place", "status": "FAIL",
                                   "metrics": {"WNS": -0.500, "TNS": -20.0},
                                   "job": {"status": "FAIL", "runtime": "60m"}},
                         "route": {"step": "route", "status": "PENDING",
                                   "metrics": {}, "job": {}},
                     })
        versions = load_versions([os.path.join(tmp, d)
                                  for d in os.listdir(tmp)], config)
        assert versions[0].status == OverallStatus.FAIL


def test_load_with_running():
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        make_run_dir(tmp, "2026-01-01_1200_chip_C", {"version": "chip_C"},
                     {
                         "init": {"step": "init", "status": "SUCCESS",
                                  "metrics": {}, "job": {}},
                         "place": {"step": "place", "status": "RUNNING",
                                   "metrics": {"WNS": -0.150, "TNS": -5.0},
                                   "job": {"status": "RUNNING", "runtime": "10m"}},
                         # route.json missing = PENDING
                     })
        versions = load_versions([os.path.join(tmp, d)
                                  for d in os.listdir(tmp)], config)
        assert versions[0].status == OverallStatus.RUNNING
        assert versions[0].latest_step == "place"
        assert versions[0].steps[2].status == StepStatus.PENDING


def test_missing_step_file():
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        dir_path = os.path.join(tmp, "2026-01-01_1200_chip_D")
        os.makedirs(dir_path)
        with open(os.path.join(dir_path, "run_info.json"), "w") as f:
            json.dump({"version": "chip_D"}, f)
        # No step JSON files at all
        versions = load_versions([dir_path], config)
        assert len(versions) == 1
        v = versions[0]
        assert v.status == OverallStatus.RUNNING
        assert all(s.status == StepStatus.PENDING for s in v.steps)
        assert v.latest_step == ""


def test_dotted_metric_key():
    """Metrics with dots in key should read from nested dict."""
    # This tests the current behavior — metrics are read flat from metrics dict
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        make_run_dir(tmp, "2026-01-01_1200_chip_E", {"version": "chip_E"},
                     {
                         "init": {"step": "init", "status": "SUCCESS",
                                  "metrics": {"WNS": -0.010, "TNS": 0.0},
                                  "job": {}},
                         "place": {"step": "place", "status": "SUCCESS",
                                   "metrics": {"WNS": -0.020, "TNS": -0.5},
                                   "job": {}},
                         "route": {"step": "route", "status": "SUCCESS",
                                   "metrics": {},
                                   "job": {}},
                     })
        versions = load_versions([os.path.join(tmp, d)
                                  for d in os.listdir(tmp)], config)
        # route has no WNS/TNS in metrics → should be None
        assert versions[0].steps[2].metrics["WNS"] is None
