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
