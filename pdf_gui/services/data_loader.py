import json
import os
from typing import List

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import (Job, OverallStatus, Step, StepStatus,
                                     Version, compute_latest_step_name)
from pdf_gui.utils.log import get_logger

log = get_logger()


def _parse_step_status(raw: str) -> StepStatus:
    try:
        return StepStatus(raw.upper())
    except (ValueError, AttributeError):
        return StepStatus.PENDING


def derive_overall(steps: List[Step]) -> OverallStatus:
    statuses = {s.status for s in steps}
    if StepStatus.FAIL in statuses:
        return OverallStatus.FAIL
    if StepStatus.RUNNING in statuses:
        return OverallStatus.RUNNING
    if statuses == {StepStatus.SUCCESS}:
        return OverallStatus.SUCCESS
    if StepStatus.PENDING in statuses:
        return OverallStatus.PENDING
    return OverallStatus.PENDING  # no steps → PENDING




def load_versions(run_dirs: List[str], config: FlowConfig) -> List[Version]:
    versions = []

    for dir_path in run_dirs:
        run_info_path = os.path.join(dir_path, "run_info.json")
        version_name = os.path.basename(dir_path)
        if os.path.isfile(run_info_path):
            with open(run_info_path, "r", encoding="utf-8") as f:
                run_info = json.load(f)
            version_name = run_info.get("version", version_name)
        else:
            log.warning("run_info.json not found in %s, using dir name", dir_path)

        steps = []
        all_step_names = []
        seen = set()
        for g in config.step_groups:
            for sn in [s.name for s in g.steps]:
                if sn not in seen:
                    seen.add(sn)
                    all_step_names.append(sn)
        all_metric_keys = []
        seen_m = set()
        for g in config.step_groups:
            for m in g.metrics:
                if m.key not in seen_m:
                    seen_m.add(m.key)
                    all_metric_keys.append(m.key)

        for step_name in all_step_names:
            step_json_path = os.path.join(dir_path, f"{step_name}.json")
            if not os.path.isfile(step_json_path):
                log.debug("Step file not found: %s (skipped)", step_json_path)
                continue

            try:
                with open(step_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                log.error("Invalid JSON in %s: %s", step_json_path, e)
                continue

            status = _parse_step_status(data.get("status", ""))

            metrics = {}
            for mk in all_metric_keys:
                val = data.get("metrics", {}).get(mk)
                metrics[mk] = float(val) if val is not None else None

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
                name=step_name,
                status=status,
                metrics=metrics,
                job=job,
            ))

        overall = derive_overall(steps)
        latest = compute_latest_step_name(steps)

        versions.append(Version(
            name=version_name,
            dir_path=dir_path,
            status=overall,
            steps=steps,
            latest_step=latest,
        ))

    return versions
