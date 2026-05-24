"""Tests for GroupedVersion creation and make_grouped_versions."""

from pdf_gui.models.run_data import (GroupedVersion, OverallStatus, Step,
                                     StepStatus, Version,
                                     compute_latest_step_name,
                                     make_grouped_versions)
from pdf_gui.services.data_loader import derive_overall


def test_make_grouped_versions_filters():
    """Only steps in the group are included."""
    versions = [
        Version(name="v1", dir_path="/tmp", status=OverallStatus.SUCCESS,
                steps=[
                    Step(name="init", status=StepStatus.SUCCESS, metrics={}),
                    Step(name="place", status=StepStatus.SUCCESS, metrics={}),
                    Step(name="cts", status=StepStatus.SUCCESS, metrics={}),
                ], latest_step="cts"),
    ]
    result = make_grouped_versions(versions, ["init", "place"], derive_overall)
    assert len(result) == 1
    gv = result[0]
    assert gv.name == "v1"
    assert [s.name for s in gv.steps] == ["init", "place"]
    assert "cts" not in [s.name for s in gv.steps]


def test_make_grouped_versions_derives_status():
    """Status is derived from only the group steps."""
    versions = [
        Version(name="v1", dir_path="/tmp", status=OverallStatus.SUCCESS,
                steps=[
                    Step(name="init", status=StepStatus.SUCCESS, metrics={}),
                    Step(name="place", status=StepStatus.FAIL, metrics={}),
                    Step(name="cts", status=StepStatus.SUCCESS, metrics={}),
                ], latest_step="cts"),
    ]
    # Group with only SUCCESS steps → SUCCESS
    result_ok = make_grouped_versions(versions, ["init", "cts"], derive_overall)
    assert result_ok[0].status == OverallStatus.SUCCESS

    # Group including the FAIL step → FAIL
    result_fail = make_grouped_versions(versions, ["place"], derive_overall)
    assert result_fail[0].status == OverallStatus.FAIL


def test_make_grouped_versions_latest_step():
    """latest_step is specific to the group, not global."""
    versions = [
        Version(name="v1", dir_path="/tmp", status=OverallStatus.SUCCESS,
                steps=[
                    Step(name="init", status=StepStatus.SUCCESS, metrics={}),
                    Step(name="cts", status=StepStatus.PENDING, metrics={}),
                ], latest_step="init"),
    ]
    # Group with only init → latest_step = "init"
    result = make_grouped_versions(versions, ["init"], derive_overall)
    assert result[0].latest_step == "init"


def test_make_grouped_versions_excludes_empty():
    """Version with 0 steps in group is excluded from result."""
    versions = [
        Version(name="v1", dir_path="/tmp", status=OverallStatus.SUCCESS,
                steps=[
                    Step(name="init", status=StepStatus.SUCCESS, metrics={}),
                ], latest_step="init"),
    ]
    result = make_grouped_versions(versions, ["place"], derive_overall)
    assert len(result) == 0


def test_compute_latest_step_name():
    steps = [
        Step(name="init", status=StepStatus.SUCCESS, metrics={}),
        Step(name="place", status=StepStatus.PENDING, metrics={}),
        Step(name="cts", status=StepStatus.PENDING, metrics={}),
    ]
    assert compute_latest_step_name(steps) == "init"
    assert compute_latest_step_name(steps[1:]) == ""
