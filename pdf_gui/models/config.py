from dataclasses import dataclass, field
from typing import Dict, List, Optional

import os

import yaml

from pdf_gui.utils.log import get_logger

log = get_logger()


@dataclass
class MetricConfig:
    key: str
    label: str = ""
    format: str = ".3f"
    reports: List[str] = field(default_factory=list)
    pictures: List[str] = field(default_factory=list)
    step_reports: Dict[str, List[str]] = field(default_factory=dict)
    step_pictures: Dict[str, List[str]] = field(default_factory=dict)

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
class DatabaseConfig:
    """A database that can be opened from the GUI for a step.

    Each entry represents one EDA tool database associated with a step.
    The ``command`` template supports {version}, {step}, {run_dir}, {label}
    placeholder substitution.
    """
    label: str
    command: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = "DB"


@dataclass
class StepConfig:
    name: str
    label: str = ""
    logs: List[str] = field(default_factory=list)
    databases: List[DatabaseConfig] = field(default_factory=list)

    def __post_init__(self):
        if not self.label:
            self.label = self.name.title()


@dataclass
class StepGroupConfig:
    name: str
    label: str = ""
    steps: List[StepConfig] = field(default_factory=list)
    metrics: List[MetricConfig] = field(default_factory=list)

    def __post_init__(self):
        if not self.label:
            self.label = self.name
        if self.steps and isinstance(self.steps[0], str):
            self.steps = [StepConfig(name=s) for s in self.steps]


@dataclass
class StatusColors:
    SUCCESS: str = "#4CAF50"
    FAIL: str = "#F44336"
    RUNNING: str = "#2196F3"
    PENDING: str = "#FF9800"


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
    ui_font: str = "system-ui"
    data_font: str = "Consolas"
    auto_refresh_seconds: int = 0
    refresh_command: str = ""
    report_command: str = ""
    picture_command: str = ""
    database_command: str = ""
    step_groups: List[StepGroupConfig] = field(default_factory=list)

    def __post_init__(self):
        if not self.step_groups and self.steps:
            self.step_groups = [StepGroupConfig(
                name="All",
                steps=list(self.steps),
                metrics=list(self.metrics),
            )]
            self.metrics = []


def load_config(path: str) -> FlowConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        log.error("Failed to load config '%s': %s", path, e)
        return FlowConfig()

    flow_name = raw.get("flow_name", "PD Flow")

    if not raw.get("step_groups"):
        if raw.get("steps") or raw.get("metrics"):
            log.warning("Config uses flat 'steps'/'metrics' — these are deprecated. "
                        "Use 'step_groups' instead. Flat entries will be ignored.")
        return FlowConfig()

    step_groups = []
    for g in raw["step_groups"]:
            group_metrics = []
            for gm in g.get("metrics", []):
                sr = {}
                for sn, paths in gm.get("step_reports", {}).items():
                    sr[sn] = paths if isinstance(paths, list) else [paths]
                sp = {}
                for sn, paths in gm.get("step_pictures", {}).items():
                    sp[sn] = paths if isinstance(paths, list) else [paths]
                group_metrics.append(MetricConfig(
                    key=gm["key"],
                    label=gm.get("label", ""),
                    format=gm.get("format", ".3f"),
                    reports=gm.get("reports", []),
                    pictures=gm.get("pictures", []),
                    step_reports=sr,
                    step_pictures=sp,
                ))
            group_step_configs = []
            for gs in g.get("steps", []):
                if isinstance(gs, str):
                    group_step_configs.append(StepConfig(name=gs))
                else:
                    db_list = []
                    for db in gs.get("databases", []):
                        db_list.append(DatabaseConfig(
                            label=db.get("label", db.get("command", "DB")),
                            command=db.get("command", ""),
                        ))
                    group_step_configs.append(StepConfig(
                        name=gs["name"], label=gs.get("label", ""),
                        logs=gs.get("logs", []),
                        databases=db_list,
                    ))
            step_groups.append(StepGroupConfig(
                name=g["name"], label=g.get("label", ""),
                steps=group_step_configs, metrics=group_metrics,
            ))
    # (auto-convert removed — flat configs now rejected above)

    steps = []
    metrics = []

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

    default_font = raw.get("default_font", "Consolas")
    return FlowConfig(
        flow_name=flow_name,
        steps=steps,
        metrics=metrics,
        job_columns=job_columns,
        colors=colors,
        icons=icons,
        default_font=default_font,
        default_font_size=raw.get("default_font_size", 10),
        ui_font=raw.get("ui_font", default_font),
        data_font=raw.get("data_font", default_font),
        auto_refresh_seconds=raw.get("auto_refresh_seconds", 0),
        refresh_command=raw.get("refresh_command", ""),
        report_command=raw.get("report_command", ""),
        picture_command=raw.get("picture_command", ""),
        database_command=raw.get("database_command", ""),
        step_groups=step_groups,
    )


def validate_config(config: FlowConfig):
    """Sanity check config and log warnings for potential issues."""
    log.info("--- Config Sanity Check ---")

    all_steps = []
    for g in config.step_groups:
        for sn in [s.name for s in g.steps]:
            if sn not in all_steps:
                all_steps.append(sn)
    eff_metrics = []
    for g in config.step_groups:
        for m in g.metrics:
            if m.key not in eff_metrics:
                eff_metrics.append(m.key)

    if not all_steps and not config.step_groups:
        log.warning("No steps defined — table will be empty")

    if config.step_groups:
        log.info("Step groups: %d groups, %d unique steps, %d unique metrics",
                 len(config.step_groups), len(all_steps), len(eff_metrics))

    if len(all_steps) != len(set(all_steps)):
        seen = set()
        for s in all_steps:
            if s in seen:
                log.warning("Duplicate step name: '%s'", s)
            seen.add(s)

    if not eff_metrics and not config.step_groups:
        log.warning("No metrics defined — table will have no data columns")

    metric_keys = eff_metrics
    if len(metric_keys) != len(set(metric_keys)):
        seen = set()
        for k in metric_keys:
            if k in seen:
                log.warning("Duplicate metric key: '%s'", k)
            seen.add(k)

    metrics_to_check = []
    for g in config.step_groups:
        metrics_to_check.extend(g.metrics)

    for m in metrics_to_check:
        for sn in m.step_reports:
            if sn not in all_steps:
                log.warning("metric '%s' step_reports key '%s' not in steps",
                            m.key, sn)
        for sn in m.step_pictures:
            if sn not in all_steps:
                log.warning("metric '%s' step_pictures key '%s' not in steps",
                            m.key, sn)

    if config.report_command and "{file}" not in config.report_command:
        log.warning("report_command missing {file} placeholder")
    if config.picture_command and "{file}" not in config.picture_command:
        log.warning("picture_command missing {file} placeholder")

    if config.refresh_command and not os.path.isfile(
            config.refresh_command.split()[0]):
        log.warning("refresh_command not found: %s", config.refresh_command)

    eff_steps = all_steps
    log.info("--- Sanity check complete: %d steps, %d metrics ---",
             len(eff_steps), len(eff_metrics))
