"""Convert Version list to pandas DataFrame for analysis and charting."""

from typing import List

import pandas as pd

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import Version


def build_dataframe(versions: List[Version], config: FlowConfig) -> pd.DataFrame:
    """Build a DataFrame with one row per step per version.

    Columns:
        version_name, version_status, step_name, step_status,
        <metric_key>..., job_status, job_runtime, job_memory_current_mb,
        job_cpu_current_pct
    """
    metric_keys = [m.key for m in config.metrics]
    rows = []

    for v in versions:
        for step in v.steps:
            row = {
                "version_name": v.name,
                "version_status": v.status.value,
                "step_name": step.name,
                "step_status": step.status.value,
            }
            for mk in metric_keys:
                row[mk] = step.metrics.get(mk)

            if step.job:
                row["job_status"] = step.job.status.value
                row["job_runtime"] = step.job.runtime
                row["job_memory_current_mb"] = step.job.memory_current_mb
                row["job_cpu_current_pct"] = step.job.cpu_current_pct
            else:
                row["job_status"] = None
                row["job_runtime"] = None
                row["job_memory_current_mb"] = None
                row["job_cpu_current_pct"] = None

            rows.append(row)

    df = pd.DataFrame(rows)

    for mk in metric_keys:
        if mk in df.columns:
            df[mk] = pd.to_numeric(df[mk], errors="coerce")

    if "job_memory_current_mb" in df.columns:
        df["job_memory_current_mb"] = pd.to_numeric(
            df["job_memory_current_mb"], errors="coerce")
    if "job_cpu_current_pct" in df.columns:
        df["job_cpu_current_pct"] = pd.to_numeric(
            df["job_cpu_current_pct"], errors="coerce")

    return df
