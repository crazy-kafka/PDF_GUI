import json
import os
from typing import List

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import Job, OverallStatus, Step, StepStatus, Version


def _parse_step_status(raw: str) -> StepStatus:
    try:
        return StepStatus(raw.upper())
    except (ValueError, AttributeError):
        return StepStatus.PENDING


def _derive_overall(steps: List[Step]) -> OverallStatus:
    statuses = {s.status for s in steps}
    if StepStatus.FAIL in statuses:
        return OverallStatus.FAIL
    if StepStatus.RUNNING in statuses:
        return OverallStatus.RUNNING
    if statuses == {StepStatus.SUCCESS}:
        return OverallStatus.SUCCESS
    if len(steps) >= 2 and steps[-1].status == StepStatus.PENDING \
            and steps[-2].status == StepStatus.SUCCESS:
        return OverallStatus.PENDING
    return OverallStatus.RUNNING


def _latest_step_name(steps: List[Step]) -> str:
    for s in reversed(steps):
        if s.status != StepStatus.PENDING:
            return s.name
    return ""


def load_versions(run_dirs: List[str], config: FlowConfig) -> List[Version]:
    versions = []

    for dir_path in run_dirs:
        run_info_path = os.path.join(dir_path, "run_info.json")
        version_name = os.path.basename(dir_path)
        if os.path.isfile(run_info_path):
            with open(run_info_path, "r", encoding="utf-8") as f:
                run_info = json.load(f)
            version_name = run_info.get("version", version_name)

        steps = []
        for sc in config.steps:
            step_json_path = os.path.join(dir_path, f"{sc.name}.json")
            if not os.path.isfile(step_json_path):
                continue

            with open(step_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            status = _parse_step_status(data.get("status", ""))

            metrics = {}
            for mc in config.metrics:
                val = data.get("metrics", {}).get(mc.key)
                metrics[mc.key] = float(val) if val is not None else None

            job = None
            job_raw = data.get("job")
            if job_raw:
                job = Job(
                    job_id=job_raw.get("job_id", ""),
                    status=_parse_step_status(job_raw.get("status", "")),
                    memory_current_mb=float(job_raw.get("memory_current_mb", 0)),
                    memory_max_mb=float(job_raw.get("memory_max_mb", 0)),
                    memory_avg_mb=float(job_raw.get("memory_avg_mb", 0)),
                    cpu_current_pct=float(job_raw.get("cpu_current_pct", 0)),
                    cpu_max_pct=float(job_raw.get("cpu_max_pct", 0)),
                    cpu_avg_pct=float(job_raw.get("cpu_avg_pct", 0)),
                    runtime=str(job_raw.get("runtime", "")),
                )

            steps.append(Step(
                name=sc.name,
                status=status,
                metrics=metrics,
                job=job,
            ))

        overall = _derive_overall(steps)
        latest = _latest_step_name(steps)

        versions.append(Version(
            name=version_name,
            dir_path=dir_path,
            status=overall,
            steps=steps,
            latest_step=latest,
        ))

    return versions
