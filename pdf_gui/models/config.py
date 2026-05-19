from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class MetricConfig:
    key: str
    label: str = ""
    format: str = ".3f"
    reports: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.label:
            self.label = self.key


@dataclass
class JobColumnConfig:
    key: str
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.key.replace("_", " ").title()


@dataclass
class StepConfig:
    name: str
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.name.title()


@dataclass
class StatusColors:
    SUCCESS: str = "#4CAF50"
    FAIL: str = "#F44336"
    RUNNING: str = "#2196F3"
    PENDING: str = "#9E9E9E"


@dataclass
class StatusIcons:
    SUCCESS: str = "✓"
    FAIL: str = "✗"
    RUNNING: str = "⟳"
    PENDING: str = "○"


@dataclass
class FlowConfig:
    flow_name: str = "PD Flow"
    steps: List[StepConfig] = field(default_factory=list)
    metrics: List[MetricConfig] = field(default_factory=list)
    job_columns: List[JobColumnConfig] = field(default_factory=list)
    colors: StatusColors = field(default_factory=StatusColors)
    icons: StatusIcons = field(default_factory=StatusIcons)
    default_font: str = "Consolas"
    default_font_size: int = 10
    auto_refresh_seconds: int = 0
    refresh_command: str = ""
    report_command: str = ""


def load_config(path: str) -> FlowConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    flow_name = raw.get("flow_name", "PD Flow")

    steps = [StepConfig(name=s["name"], label=s.get("label", ""))
             for s in raw.get("steps", [])]

    metrics = []
    for m in raw.get("metrics", []):
        metrics.append(MetricConfig(
            key=m["key"],
            label=m.get("label", ""),
            format=m.get("format", ".3f"),
            reports=m.get("reports", []),
        ))

    job_columns = []
    for jc in raw.get("job_columns", []):
        job_columns.append(JobColumnConfig(
            key=jc["key"],
            label=jc.get("label", ""),
        ))

    colors_raw = raw.get("colors", {})
    colors = StatusColors(
        SUCCESS=colors_raw.get("SUCCESS", "#4CAF50"),
        FAIL=colors_raw.get("FAIL", "#F44336"),
        RUNNING=colors_raw.get("RUNNING", "#2196F3"),
        PENDING=colors_raw.get("PENDING", "#9E9E9E"),
    )

    icons_raw = raw.get("icons", {})
    icons = StatusIcons(
        SUCCESS=icons_raw.get("SUCCESS", "✓"),
        FAIL=icons_raw.get("FAIL", "✗"),
        RUNNING=icons_raw.get("RUNNING", "⟳"),
        PENDING=icons_raw.get("PENDING", "○"),
    )

    return FlowConfig(
        flow_name=flow_name,
        steps=steps,
        metrics=metrics,
        job_columns=job_columns,
        colors=colors,
        icons=icons,
        default_font=raw.get("default_font", "Consolas"),
        default_font_size=raw.get("default_font_size", 10),
        auto_refresh_seconds=raw.get("auto_refresh_seconds", 0),
        refresh_command=raw.get("refresh_command", ""),
        report_command=raw.get("report_command", ""),
    )
