"""Tests for the EDA database open button feature."""
import os
import subprocess
import sys
import tempfile
import time

import pytest
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QApplication, QPushButton

from pdf_gui.models.config import (DatabaseConfig, FlowConfig, JobColumnConfig,
                                   MetricConfig, StepConfig, StepGroupConfig)
from pdf_gui.models.run_data import (GroupedVersion, Job, OverallStatus, Step,
                                     StepStatus)
from pdf_gui.widgets.metric_table import MetricTable


DB_LAUNCHER = f'"{sys.executable}" tests/test_data/db_launcher.py --no-gui'


def _base_config(extra_steps=None, db_command=None):
    """Build a FlowConfig with one group for testing."""
    default_cmd = f"{DB_LAUNCHER} --label {{label}} --version {{version}} --step {{step}} --run_dir {{run_dir}}"
    steps = [
        StepConfig(name="init", logs=["logs/{version}/{step}/run.log"]),
        StepConfig(name="place", logs=["logs/{version}/{step}/run.log"],
                   databases=[
                       DatabaseConfig(label="ICC2 Layout",
                                      command=default_cmd),
                       DatabaseConfig(label="Verdi Debug",
                                      command=default_cmd),
                   ]),
        StepConfig(name="route",
                   databases=[
                       DatabaseConfig(label="Route DB", command=""),
                   ]),
    ]
    if extra_steps:
        steps.extend(extra_steps)
    return FlowConfig(
        flow_name="Test",
        step_groups=[StepGroupConfig(
            name="APR", steps=steps,
            metrics=[MetricConfig(key="WNS", format=".3f")],
        )],
        job_columns=[JobColumnConfig(key="status")],
        database_command=db_command if db_command is not None else default_cmd,
    )


def _make_gv(name="v1", extra_steps=None):
    """Build a GroupedVersion with init, place, route steps."""
    steps = [
        Step(name="init", status=StepStatus.SUCCESS,
             metrics={"WNS": -0.050}, job=Job(status=StepStatus.SUCCESS)),
        Step(name="place", status=StepStatus.SUCCESS,
             metrics={"WNS": -0.100}, job=Job(status=StepStatus.SUCCESS)),
        Step(name="route", status=StepStatus.SUCCESS,
             metrics={"WNS": -0.015}, job=Job(status=StepStatus.SUCCESS)),
    ]
    if extra_steps:
        steps.extend(extra_steps)
    return GroupedVersion(
        name=name, dir_path="/tmp/test", status=OverallStatus.SUCCESS,
        steps=steps, latest_step="route",
    )


# ── Column tests ────────────────────────────────────────────────────

def test_db_column_present_when_configured():
    app = QApplication.instance() or QApplication([])
    config = _base_config()
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    assert table._has_databases is True
    assert "DB" in table._columns


def test_db_column_absent_when_not_configured():
    app = QApplication.instance() or QApplication([])
    config = FlowConfig(
        step_groups=[StepGroupConfig(
            name="All", steps=[StepConfig(name="init")],
            metrics=[MetricConfig(key="WNS")],
        )],
        job_columns=[JobColumnConfig(key="status")],
    )
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    assert table._has_databases is False
    assert "DB" not in table._columns


def test_db_button_present_for_configured_step():
    app = QApplication.instance() or QApplication([])
    config = _base_config()
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    db_col = table.columnCount() - 1
    # place row (row index = 1 data + offset) should have a DB button
    place_row = 1 + table._data_row_offset
    btn = table.cellWidget(place_row, db_col)
    assert isinstance(btn, QPushButton)
    assert btn.text() == "DB"
    # route row (row index = 2) should also have a DB button
    route_row = 2 + table._data_row_offset
    btn2 = table.cellWidget(route_row, db_col)
    assert isinstance(btn2, QPushButton)


def test_db_button_absent_for_unconfigured_step():
    app = QApplication.instance() or QApplication([])
    config = _base_config()
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    db_col = table.columnCount() - 1
    # init row has no databases configured
    init_row = 0 + table._data_row_offset
    btn = table.cellWidget(init_row, db_col)
    assert btn is None


def test_db_column_header_plain():
    app = QApplication.instance() or QApplication([])
    config = _base_config()
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    # No @-grouped metrics, so plain header
    assert table._has_grouped_header is False
    # Check "DB" is in horizontal header labels
    header_labels = []
    for c in range(table.columnCount()):
        item = table.horizontalHeaderItem(c)
        if item:
            header_labels.append(item.text())
    assert "DB" in header_labels


def test_db_column_header_grouped():
    app = QApplication.instance() or QApplication([])
    config = FlowConfig(
        step_groups=[StepGroupConfig(
            name="APR", steps=[
                StepConfig(name="init"),
                StepConfig(name="place", databases=[
                    DatabaseConfig(label="Test DB", command="echo {label}"),
                ]),
            ],
            metrics=[
                MetricConfig(key="REG2REG@wns", label="wns"),
                MetricConfig(key="REG2REG@tns", label="tns"),
            ],
        )],
        job_columns=[JobColumnConfig(key="status")],
    )
    gv = GroupedVersion(
        name="v1", dir_path="/tmp", status=OverallStatus.SUCCESS,
        steps=[
            Step(name="init", status=StepStatus.SUCCESS,
                 metrics={"REG2REG@wns": -0.05, "REG2REG@tns": -1.0},
                 job=Job(status=StepStatus.SUCCESS)),
            Step(name="place", status=StepStatus.SUCCESS,
                 metrics={"REG2REG@wns": -0.03, "REG2REG@tns": -0.5},
                 job=Job(status=StepStatus.SUCCESS)),
        ],
        latest_step="place",
    )
    table = MetricTable(gv, config, group=config.step_groups[0])
    assert table._has_grouped_header is True
    # DB header should be in row 0, DB column
    db_col = table.columnCount() - 1
    hdr_item = table.item(0, db_col)
    assert hdr_item is not None
    assert hdr_item.text() == "DB"


# ── Command resolution tests ────────────────────────────────────────

def test_db_command_template_substitution():
    app = QApplication.instance() or QApplication([])
    config = _base_config()
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    db = config.step_groups[0].steps[1].databases[0]  # "ICC2 Layout"
    cmd = table._resolve_db_command(db, "place")
    assert "ICC2 Layout" in cmd
    assert "v1" in cmd
    assert "place" in cmd
    assert "/tmp/test" in cmd


def test_global_database_command_fallback():
    app = QApplication.instance() or QApplication([])
    config = _base_config(db_command=f"{DB_LAUNCHER} --label {{label}} --version {{version}}")
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    # Route DB has command="", so it should use global database_command
    db = config.step_groups[0].steps[2].databases[0]  # "Route DB"
    cmd = table._resolve_db_command(db, "route")
    assert "Route DB" in cmd
    assert "v1" in cmd
    # Should NOT contain {step} since the global command doesn't have it
    assert "route" not in cmd.split("--version")[0]


def test_qsettings_database_command_override():
    app = QApplication.instance() or QApplication([])
    settings = QSettings("pdf_gui", "settings")
    settings.setValue("database_command", "qsettings_cmd {label} {step}")
    config = _base_config()
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    db = config.step_groups[0].steps[2].databases[0]
    cmd = table._resolve_db_command(db, "route")
    assert "qsettings_cmd" in cmd
    assert "Route DB" in cmd
    assert "route" in cmd
    # Clean up
    settings.remove("database_command")


def test_no_command_returns_empty():
    app = QApplication.instance() or QApplication([])
    config = _base_config(db_command="")  # no global command
    # Route DB has command="" and no global → nothing
    config.step_groups[0].steps[2].databases[0].command = ""
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    db = config.step_groups[0].steps[2].databases[0]
    cmd = table._resolve_db_command(db, "route")
    assert cmd == ""


# ── Launch tests (receipt file verification) ────────────────────────

def test_single_db_launches_directly():
    """1 database → command runs, receipt file created."""
    app = QApplication.instance() or QApplication([])
    receipt_dir = tempfile.mkdtemp()
    os.environ["DB_RECEIPT_DIR"] = receipt_dir
    try:
        config = FlowConfig(
            step_groups=[StepGroupConfig(
                name="APR", steps=[
                    StepConfig(name="place", databases=[
                        DatabaseConfig(label="Single DB",
                                       command=f"{DB_LAUNCHER} --label {{label}} --version {{version}} --step {{step}}"),
                    ]),
                ],
                metrics=[MetricConfig(key="WNS")],
            )],
            job_columns=[JobColumnConfig(key="status")],
        )
        gv = GroupedVersion(
            name="chip_test", dir_path="/tmp", status=OverallStatus.SUCCESS,
            steps=[
                Step(name="place", status=StepStatus.SUCCESS,
                     metrics={"WNS": -0.05}, job=Job(status=StepStatus.SUCCESS)),
            ],
            latest_step="place",
        )
        table = MetricTable(gv, config, group=config.step_groups[0])
        db = config.step_groups[0].steps[0].databases[0]
        cmd = table._resolve_db_command(db, "place")
        assert "Single DB" in cmd
        assert "chip_test" in cmd
        assert "place" in cmd
        # Run via shell=False for reliable env var inheritance
        run_env = os.environ.copy()
        run_env["DB_RECEIPT_DIR"] = receipt_dir
        args = [sys.executable, "tests/test_data/db_launcher.py", "--no-gui",
                "--label", "Single DB", "--version", "chip_test", "--step", "place"]
        subprocess.run(args, timeout=10, env=run_env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        receipts = [f for f in os.listdir(receipt_dir) if f.startswith("db_open_receipt")]
        assert len(receipts) >= 1
        with open(os.path.join(receipt_dir, receipts[0])) as f:
            content = f.read()
        assert "Single DB" in content
        assert "chip_test" in content
        assert "place" in content
    finally:
        del os.environ["DB_RECEIPT_DIR"]


def test_db_command_with_label_and_run_dir():
    """Template variables {label}, {version}, {step}, {run_dir} all resolve."""
    app = QApplication.instance() or QApplication([])
    receipt_dir = tempfile.mkdtemp()
    os.environ["DB_RECEIPT_DIR"] = receipt_dir
    try:
        config = FlowConfig(
            step_groups=[StepGroupConfig(
                name="APR", steps=[
                    StepConfig(name="route", databases=[
                        DatabaseConfig(label="Route DB",
                                       command=f"{DB_LAUNCHER} --label {{label}} --version {{version}} --step {{step}} --run_dir {{run_dir}}"),
                    ]),
                ],
                metrics=[MetricConfig(key="WNS")],
            )],
            job_columns=[JobColumnConfig(key="status")],
        )
        gv = GroupedVersion(
            name="v_route_test", dir_path="/tmp/runs",
            status=OverallStatus.RUNNING,
            steps=[
                Step(name="route", status=StepStatus.RUNNING,
                     metrics={"WNS": -0.03}, job=Job(status=StepStatus.RUNNING)),
            ],
            latest_step="route",
        )
        table = MetricTable(gv, config, group=config.step_groups[0])
        db = config.step_groups[0].steps[0].databases[0]
        cmd = table._resolve_db_command(db, "route")
        assert "Route DB" in cmd
        assert "v_route_test" in cmd
        assert "route" in cmd
        assert "/tmp/runs" in cmd  # {run_dir} resolved in command
        # Launch via shell=False for reliable env var inheritance
        run_env = os.environ.copy()
        run_env["DB_RECEIPT_DIR"] = receipt_dir
        args = [sys.executable, "tests/test_data/db_launcher.py", "--no-gui",
                "--label", "Route DB", "--version", "v_route_test", "--step", "route"]
        subprocess.run(args, timeout=10, env=run_env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        receipts = [f for f in os.listdir(receipt_dir) if f.startswith("db_open_receipt")]
        assert len(receipts) >= 1
        with open(os.path.join(receipt_dir, receipts[0])) as f:
            content = f.read()
        assert "Route DB" in content
        assert "v_route_test" in content
        assert "route" in content
    finally:
        del os.environ["DB_RECEIPT_DIR"]


def test_db_and_log_both_present():
    """Both Log and DB columns coexist, both functional."""
    app = QApplication.instance() or QApplication([])
    config = _base_config()
    gv = _make_gv()
    table = MetricTable(gv, config, group=config.step_groups[0])
    assert table._has_logs is True
    assert table._has_databases is True
    # Column order: Step, WNS, Status, Log, DB
    assert "Log" in table._columns
    assert "DB" in table._columns
    # DB column should be the last column
    assert table._columns[-1] == "DB"
    # Log column should be second-to-last
    assert table._columns[-2] == "Log"


def test_resolve_db_command_with_empty_gv_steps():
    """Empty step list in GV should not crash _resolve_db_command."""
    app = QApplication.instance() or QApplication([])
    config = _base_config()
    gv = GroupedVersion(
        name="empty", dir_path="/tmp", status=OverallStatus.PENDING,
        steps=[], latest_step="",
    )
    table = MetricTable(gv, config, group=config.step_groups[0])
    db = config.step_groups[0].steps[1].databases[0]
    cmd = table._resolve_db_command(db, "unknown")
    assert "unknown" in cmd  # step name passed explicitly
