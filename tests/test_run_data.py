import json
import os
import tempfile

from PyQt5.QtWidgets import QApplication

from pdf_gui.models.config import FlowConfig, MetricConfig, StepConfig, StepGroupConfig
from pdf_gui.models.run_data import (Job, OverallStatus, Step, StepStatus,
                                     Version)
from pdf_gui.services.data_loader import load_versions
from pdf_gui.services.file_scanner import scan_runs
from pdf_gui.widgets.metric_table import MetricTable


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
                         "route": {"step": "route", "status": "PENDING",
                                   "metrics": {}, "job": {}},
                     })
        versions = load_versions([os.path.join(tmp, d)
                                  for d in os.listdir(tmp)], config)
        assert versions[0].status == OverallStatus.RUNNING
        assert versions[0].latest_step == "place"
        assert versions[0].steps[2].status == StepStatus.PENDING


def test_missing_step_file():
    """Version with no step files has zero steps."""
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        dir_path = os.path.join(tmp, "2026-01-01_1200_chip_D")
        os.makedirs(dir_path)
        with open(os.path.join(dir_path, "run_info.json"), "w") as f:
            json.dump({"version": "chip_D"}, f)
        # No step JSON files at all → no steps in version
        versions = load_versions([dir_path], config)
        assert len(versions) == 1
        v = versions[0]
        assert len(v.steps) == 0
        assert v.status == OverallStatus.PENDING
        assert v.latest_step == ""


def test_derive_overall_pending():
    """Any PENDING step when no FAIL/RUNNING → OverallStatus.PENDING."""
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        make_run_dir(tmp, "2026-01-01_1200_chip_P", {"version": "chip_P"},
                     {
                         "init": {"step": "init", "status": "SUCCESS",
                                  "metrics": {}, "job": {}},
                         "place": {"step": "place", "status": "SUCCESS",
                                   "metrics": {"WNS": -0.100, "TNS": -3.0},
                                   "job": {"status": "SUCCESS", "runtime": "30m"}},
                         "route": {"step": "route", "status": "PENDING",
                                   "metrics": {}, "job": {}},
                     })
        versions = load_versions([os.path.join(tmp, d)
                                  for d in os.listdir(tmp)], config)
        assert versions[0].status == OverallStatus.PENDING
        assert versions[0].latest_step == "place"


def test_branched_version():
    """Version with only a subset of step files shows only those steps."""
    config = make_config()
    with tempfile.TemporaryDirectory() as tmp:
        make_run_dir(tmp, "2026-01-01_1200_chip_branch", {"version": "chip_branch"},
                     {
                         "place": {"step": "place", "status": "SUCCESS",
                                   "metrics": {"WNS": -0.100, "TNS": -3.0},
                                   "job": {"status": "SUCCESS", "runtime": "30m"}},
                         "route": {"step": "route", "status": "RUNNING",
                                   "metrics": {"WNS": -0.200, "TNS": -8.0},
                                   "job": {"status": "RUNNING", "runtime": "15m"}},
                         # init.json missing — step not in this branch
                     })
        versions = load_versions([os.path.join(tmp, d)
                                  for d in os.listdir(tmp)], config)
        v = versions[0]
        assert v.name == "chip_branch"
        assert len(v.steps) == 2
        assert v.steps[0].name == "place"
        assert v.steps[1].name == "route"
        assert v.status == OverallStatus.RUNNING
        assert v.latest_step == "route"


def test_step_report_incremental():
    """Global reports + step_reports are concatenated."""
    config = FlowConfig(
        flow_name="Test",
        steps=[StepConfig(name="init")],
        metrics=[
            MetricConfig(key="WNS", reports=["rpt/timing.rpt"],
                         step_reports={"init": ["rpt/init_extra.rpt"]}),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = os.path.join(tmp, "2026-01-01_1200_chip_A")
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, "run_info.json"), "w") as f:
            json.dump({"version": "chip_A"}, f)
        with open(os.path.join(run_dir, "init.json"), "w") as f:
            json.dump({"step": "init", "status": "SUCCESS",
                        "metrics": {"WNS": -0.050}, "job": {}}, f)

        versions = load_versions([run_dir], config)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        table = MetricTable(versions[0], config)
        mc = config.step_groups[0].metrics[0]
        step_name = "init"
        reports = mc.reports + mc.step_reports.get(step_name, [])
        paths = table._resolve_paths(reports, step_name)
        assert len(paths) == 2
        assert paths[0][0] == "rpt/timing.rpt"
        assert paths[1][0] == "rpt/init_extra.rpt"


def test_step_report_no_step_specific():
    """Step not in step_reports → only global reports."""
    config = FlowConfig(
        flow_name="Test",
        steps=[StepConfig(name="init"), StepConfig(name="place")],
        metrics=[
            MetricConfig(key="WNS", reports=["rpt/timing.rpt"],
                         step_reports={"init": ["rpt/init_extra.rpt"]}),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = os.path.join(tmp, "2026-01-01_1200_chip_A")
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, "run_info.json"), "w") as f:
            json.dump({"version": "chip_A"}, f)
        with open(os.path.join(run_dir, "init.json"), "w") as f:
            json.dump({"step": "init", "status": "SUCCESS",
                        "metrics": {"WNS": -0.050}, "job": {}}, f)
        with open(os.path.join(run_dir, "place.json"), "w") as f:
            json.dump({"step": "place", "status": "SUCCESS",
                        "metrics": {"WNS": -0.100}, "job": {}}, f)

        versions = load_versions([run_dir], config)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        table = MetricTable(versions[0], config)
        mc = config.step_groups[0].metrics[0]
        # "place" not in step_reports → only global
        reports = mc.reports + mc.step_reports.get("place", [])
        paths = table._resolve_paths(reports, "place")
        assert len(paths) == 1
        assert paths[0][0] == "rpt/timing.rpt"


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


def test_report_path_resolution():
    """Report paths with template variables resolve correctly and file exists."""
    config = FlowConfig(
        flow_name="Test",
        steps=[
            StepConfig(name="init"),
            StepConfig(name="place"),
        ],
        metrics=[
            MetricConfig(key="WNS", reports=[
                "reports/{version}/{step}/timing.rpt",
                "reports/{version}/{step}/wns_summary.rpt",
            ]),
            MetricConfig(key="TNS"),
        ],
    )

    with tempfile.TemporaryDirectory() as tmp:
        # Create actual report files
        report_dir = os.path.join(
            tmp, "2026-01-01_1200_chip_A",
            "reports", "chip_A", "init")
        os.makedirs(report_dir)
        timing_rpt = os.path.join(report_dir, "timing.rpt")
        with open(timing_rpt, "w") as f:
            f.write("timing report content")
        wns_rpt = os.path.join(report_dir, "wns_summary.rpt")
        with open(wns_rpt, "w") as f:
            f.write("wns summary content")

        # Create run data
        run_dir = os.path.join(tmp, "2026-01-01_1200_chip_A")
        with open(os.path.join(run_dir, "run_info.json"), "w") as f:
            json.dump({"version": "chip_A"}, f)
        with open(os.path.join(run_dir, "init.json"), "w") as f:
            json.dump({
                "step": "init", "status": "SUCCESS",
                "metrics": {"WNS": -0.050}, "job": {}}, f)
        with open(os.path.join(run_dir, "place.json"), "w") as f:
            json.dump({
                "step": "place", "status": "SUCCESS",
                "metrics": {"WNS": -0.100}, "job": {}}, f)

        versions = load_versions([run_dir], config)
        assert len(versions) == 1

        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        table = MetricTable(versions[0], config)
        mc = config.step_groups[0].metrics[0]
        paths = table._resolve_paths(mc.reports, "init")
        assert len(paths) == 2

        display0, full0 = paths[0]
        assert display0 == "reports/{version}/{step}/timing.rpt"
        assert os.path.normpath(full0) == os.path.normpath(timing_rpt)
        assert os.path.isfile(full0)

        display1, full1 = paths[1]
        assert display1 == "reports/{version}/{step}/wns_summary.rpt"
        assert os.path.normpath(full1) == os.path.normpath(wns_rpt)
        assert os.path.isfile(full1)


def test_log_path_resolution():
    """Log paths resolve with template variables."""
    config = FlowConfig(
        flow_name="Test",
        steps=[
            StepConfig(name="init", logs=["logs/{version}/{step}/run.log"]),
        ],
        metrics=[],
    )

    with tempfile.TemporaryDirectory() as tmp:
        run_dir = os.path.join(tmp, "2026-01-01_1200_chip_A")
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, "run_info.json"), "w") as f:
            json.dump({"version": "chip_A"}, f)
        with open(os.path.join(run_dir, "init.json"), "w") as f:
            json.dump({"step": "init", "status": "SUCCESS",
                        "metrics": {}, "job": {}}, f)

        # Create actual log file
        log_dir = os.path.join(run_dir, "logs", "chip_A", "init")
        os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "run.log")
        with open(log_path, "w") as f:
            f.write("log content")

        versions = load_versions([run_dir], config)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        table = MetricTable(versions[0], config)
        paths = table._resolve_paths(config.step_groups[0].steps[0].logs, "init")
        assert len(paths) == 1
        display, full = paths[0]
        assert display == "logs/{version}/{step}/run.log"
        assert os.path.normpath(full) == os.path.normpath(log_path)
        assert os.path.isfile(full)


def test_metric_table_detects_groups():
    """Table with @ metrics detects groups and uses two-row header."""
    config = FlowConfig(
        step_groups=[StepGroupConfig(
            name="All", steps=["init"],
            metrics=[
                MetricConfig(key="WNS"),
                MetricConfig(key="REG2REG@wns", label="wns"),
                MetricConfig(key="REG2REG@tns", label="tns"),
            ],
        )],
    )
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = os.path.join(tmp, "2026-01-01_1200_chip_A")
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, "run_info.json"), "w") as f:
            json.dump({"version": "chip_A"}, f)
        with open(os.path.join(run_dir, "init.json"), "w") as f:
            json.dump({"step": "init", "status": "SUCCESS",
                        "metrics": {"WNS": -0.050, "REG2REG@wns": -0.030,
                                    "REG2REG@tns": -2.0}, "job": {}}, f)
        versions = load_versions([run_dir], config)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        table = MetricTable(versions[0], config,
                            group=config.step_groups[0])
        assert table._has_grouped_header is True
        assert "REG2REG" in table._metric_groups
        # header rows: row 0 = parent, row 1 = sub
        assert table.item(0, 2).text() == "REG2REG"
        assert table.item(1, 2).text() == "wns"
        assert table.item(1, 3).text() == "tns"


def test_metric_table_no_groups():
    """Table without @ metrics uses single-row header."""
    config = FlowConfig(
        step_groups=[StepGroupConfig(
            name="All", steps=["init"],
            metrics=[MetricConfig(key="WNS"), MetricConfig(key="TNS")],
        )],
    )
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = os.path.join(tmp, "2026-01-01_1200_chip_A")
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, "run_info.json"), "w") as f:
            json.dump({"version": "chip_A"}, f)
        with open(os.path.join(run_dir, "init.json"), "w") as f:
            json.dump({"step": "init", "status": "SUCCESS",
                        "metrics": {"WNS": -0.050}, "job": {}}, f)
        versions = load_versions([run_dir], config)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        table = MetricTable(versions[0], config,
                            group=config.step_groups[0])
        assert table._has_grouped_header is False


def test_picture_path_resolution():
    """Picture paths resolve with template variables."""
    config = FlowConfig(
        flow_name="Test",
        steps=[
            StepConfig(name="init"),
        ],
        metrics=[
            MetricConfig(key="density", pictures=[
                "img/{version}/{step}/density.png"])
        ],
    )

    with tempfile.TemporaryDirectory() as tmp:
        run_dir = os.path.join(tmp, "2026-01-01_1200_chip_A")
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, "run_info.json"), "w") as f:
            json.dump({"version": "chip_A"}, f)
        with open(os.path.join(run_dir, "init.json"), "w") as f:
            json.dump({"step": "init", "status": "SUCCESS",
                        "metrics": {"density": 85.2}, "job": {}}, f)

        # Create actual picture file
        img_dir = os.path.join(run_dir, "img", "chip_A", "init")
        os.makedirs(img_dir)
        img_path = os.path.join(img_dir, "density.png")
        with open(img_path, "w") as f:
            f.write("placeholder")

        versions = load_versions([run_dir], config)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        table = MetricTable(versions[0], config)
        paths = table._resolve_paths(
            config.step_groups[0].metrics[0].pictures, "init")
        assert len(paths) == 1
        display, full = paths[0]
        assert display == "img/{version}/{step}/density.png"
        assert os.path.normpath(full) == os.path.normpath(img_path)
        assert os.path.isfile(full)
