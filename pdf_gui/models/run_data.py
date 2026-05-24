from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class StepStatus(Enum):
    RUNNING = "RUNNING"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


class OverallStatus(Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    PENDING = "PENDING"


@dataclass
class Job:
    job_id: str = ""
    status: StepStatus = StepStatus.PENDING
    memory_current_mb: float = 0.0
    memory_max_mb: float = 0.0
    memory_avg_mb: float = 0.0
    cpu_current_pct: float = 0.0
    cpu_max_pct: float = 0.0
    cpu_avg_pct: float = 0.0
    runtime: str = ""


@dataclass
class Step:
    name: str
    status: StepStatus = StepStatus.PENDING
    metrics: Dict[str, Optional[float]] = field(default_factory=dict)
    job: Optional[Job] = None


@dataclass
class Version:
    name: str
    dir_path: str
    status: OverallStatus = OverallStatus.RUNNING
    steps: List[Step] = field(default_factory=list)
    latest_step: str = ""


@dataclass
class GroupedVersion:
    """A Version viewed through a single step group."""
    name: str
    dir_path: str
    status: OverallStatus
    steps: List[Step]          # only steps in this group
    latest_step: str           # latest non-PENDING step in this group


def compute_latest_step_name(steps: List[Step]) -> str:
    for s in reversed(steps):
        if s.status != StepStatus.PENDING:
            return s.name
    return ""


def make_grouped_versions(versions: List[Version],
                          group_step_names: List[str],
                          derive_fn) -> List[GroupedVersion]:
    """Filter versions to only those with steps in the group, derive per-group status."""
    step_set = set(group_step_names)
    result = []
    for v in versions:
        gv_steps = [s for s in v.steps if s.name in step_set]
        if not gv_steps:
            continue
        result.append(GroupedVersion(
            name=v.name,
            dir_path=v.dir_path,
            status=derive_fn(gv_steps),
            steps=gv_steps,
            latest_step=compute_latest_step_name(gv_steps),
        ))
    return result
