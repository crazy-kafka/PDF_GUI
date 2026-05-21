import csv
import os
import tempfile

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from pdf_gui.models.config import FlowConfig, JobColumnConfig, MetricConfig, StepConfig
from pdf_gui.models.run_data import (Job, OverallStatus, Step, StepStatus,
                                     Version)
from pdf_gui.widgets.export_dialog import ExportDialog


def make_config():
    return FlowConfig(
        flow_name="Test",
        steps=[
            StepConfig(name="init"),
            StepConfig(name="place"),
        ],
        metrics=[
            MetricConfig(key="WNS", format=".3f"),
            MetricConfig(key="TNS", format=".2f"),
        ],
        job_columns=[
            JobColumnConfig(key="status"),
            JobColumnConfig(key="runtime"),
        ],
    )


def make_version(name: str, status: OverallStatus, wns=None, tns=None,
                 step_status=StepStatus.SUCCESS):
    steps = []
    for sc in make_config().steps:
        s = Step(
            name=sc.name,
            status=step_status,
            metrics={"WNS": wns, "TNS": tns},
            job=Job(
                job_id="12345",
                status=step_status,
                runtime="10m",
            ),
        )
        steps.append(s)
    return Version(name=name, dir_path="/tmp", status=status,
                   steps=steps, latest_step=steps[-1].name)


def test_export_dialog_all_checked():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    versions = [
        make_version("v1", OverallStatus.SUCCESS),
        make_version("v2", OverallStatus.RUNNING),
        make_version("v3", OverallStatus.FAIL),
    ]
    dialog = ExportDialog(versions, make_config())
    for i in range(dialog._list.count()):
        assert dialog._list.item(i).checkState() == Qt.Checked


def test_csv_export_selected_versions():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    config = make_config()
    versions = [
        make_version("v1", OverallStatus.SUCCESS, wns=-0.050, tns=-3.45),
        make_version("v2", OverallStatus.RUNNING, wns=-0.100, tns=-8.00),
        make_version("v3", OverallStatus.FAIL, wns=-0.500, tns=-20.00),
    ]

    dialog = ExportDialog(versions, config)
    # select only v1 and v3
    dialog._list.item(0).setCheckState(Qt.Checked)
    dialog._list.item(1).setCheckState(Qt.Unchecked)
    dialog._list.item(2).setCheckState(Qt.Checked)

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.csv")
        dialog._path_edit.setText(path)
        dialog._write_csv(path, dialog._selected_versions())

        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert rows[0] == ["# Version: v1 (SUCCESS)"]
        assert rows[1] == ["Step", "WNS", "TNS", "Status", "Runtime"]
        assert rows[2][0] == "Init"
        assert rows[2][1] == "-0.050"
        assert rows[2][2] == "-3.45"
        assert rows[2][3] == "✓ SUCCESS"
        assert rows[2][4] == "10m"
        # blank separator (after 2 step rows for v1)
        assert rows[4] == []
        assert rows[5][0] == "# Version: v3 (FAIL)"
        # v2 should NOT appear
        version_headers = [r[0] for r in rows if r and r[0].startswith("# Version:")]
        assert len(version_headers) == 2
        assert "v1" in version_headers[0]
        assert "v3" in version_headers[1]


def test_csv_export_empty_selection():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    config = make_config()
    versions = [
        make_version("v1", OverallStatus.SUCCESS),
    ]
    dialog = ExportDialog(versions, config)
    dialog._list.item(0).setCheckState(Qt.Unchecked)

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "empty.csv")
        dialog._path_edit.setText(path)
        # should not raise, writes empty file with no version sections
        dialog._write_csv(path, dialog._selected_versions())
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            content = f.read()
        assert "# Version:" not in content


def test_format_switches_extension():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    dialog = ExportDialog([], make_config())
    dialog._path_edit.setText("export.csv")

    dialog._format_combo.setCurrentIndex(1)  # switch to Excel
    assert dialog._path_edit.text() == "export.xlsx"

    dialog._format_combo.setCurrentIndex(0)  # back to CSV
    assert dialog._path_edit.text() == "export.csv"
