import pytest

from pdf_gui.models.config import FlowConfig, MetricConfig, StepConfig, StepGroupConfig
from pdf_gui.models.run_data import (GroupedVersion, Job, OverallStatus, Step,
                                     StepStatus, Version)
from pdf_gui.services.dataframe_builder import build_dataframe


def make_config():
    return FlowConfig(
        step_groups=[StepGroupConfig(
            name="All",
            steps=["init", "place"],
            metrics=[MetricConfig(key="WNS"), MetricConfig(key="TNS")],
        )],
    )


def make_version(name, init_wns=None, init_tns=None,
                 place_wns=None, place_tns=None,
                 status=OverallStatus.SUCCESS, has_job=True):
    steps = []
    for step_name in ["init", "place"]:
        if step_name == "init":
            metrics = {"WNS": init_wns, "TNS": init_tns}
        else:
            metrics = {"WNS": place_wns, "TNS": place_tns}
        job = Job(job_id="123", status=StepStatus.SUCCESS, runtime="10m",
                  memory_current_mb=4096.0, cpu_current_pct=75.0) if has_job else None
        steps.append(Step(name=step_name, status=StepStatus.SUCCESS,
                          metrics=metrics, job=job))
    return GroupedVersion(name=name, dir_path="/tmp", status=status,
                          steps=steps, latest_step="place")


def test_build_dataframe_shape():
    config = make_config()
    versions = [
        make_version("v1", init_wns=-0.050, place_wns=-0.100),
        make_version("v2", init_wns=-0.080, place_wns=-0.120),
    ]
    df = build_dataframe(versions, config)
    assert len(df) == 4  # 2 versions × 2 steps
    assert "version_name" in df.columns
    assert "WNS" in df.columns
    assert "TNS" in df.columns
    assert "job_status" in df.columns


def test_build_dataframe_metric_values():
    config = make_config()
    versions = [make_version("v1", init_wns=-0.050, init_tns=-3.0)]
    df = build_dataframe(versions, config)
    row = df[(df["version_name"] == "v1") & (df["step_name"] == "init")]
    assert len(row) == 1
    assert row["WNS"].iloc[0] == pytest.approx(-0.050)
    assert row["TNS"].iloc[0] == pytest.approx(-3.0)


def test_build_dataframe_nan_handling():
    config = make_config()
    versions = [make_version("v1", init_wns=None, place_wns=-0.100)]
    df = build_dataframe(versions, config)
    row = df[(df["version_name"] == "v1") & (df["step_name"] == "init")]
    assert row["WNS"].isna().iloc[0]
    # dropna should remove only the init row
    clean = df.dropna(subset=["WNS"])
    assert len(clean) == 1  # only place row remains
    assert clean["step_name"].iloc[0] == "place"


def test_build_dataframe_missing_step():
    config = make_config()
    v = Version(name="v1", dir_path="/tmp", status=OverallStatus.SUCCESS,
                steps=[Step(name="init", status=StepStatus.SUCCESS,
                            metrics={"WNS": -0.050, "TNS": -3.0},
                            job=Job(job_id="1", status=StepStatus.SUCCESS,
                                    runtime="5m"))],
                latest_step="init")
    df = build_dataframe([v], config)
    assert len(df) == 1
    assert df["step_name"].iloc[0] == "init"


def test_build_dataframe_column_types():
    config = make_config()
    versions = [make_version("v1", init_wns=-0.050)]
    df = build_dataframe(versions, config)
    import numpy as np
    assert df["WNS"].dtype == np.float64
    assert df["version_name"].dtype == object
