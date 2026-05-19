# PDF GUI

PyQt5 desktop application for monitoring VLSI physical design flows.
Flow-agnostic: flow developers describe their flow in a YAML config file,
and the GUI dynamically renders metric tables, job status, and version tracking.

**Stack**: Python 3.9, PyQt5

## Quickstart

```bash
# Install
pip install -e .

# Generate sample data (30 realistic versions)
python tests/test_data/generate_test_data.py

# Launch with sample data
python -m pdf_gui.main --config tests/test_data/flow_config.yaml --runs tests/test_data/runs
```

## How It Works

```
flow_config.yaml     →   PDF GUI   ←   runs/YYYY-MM-DD_HHMM_name/*.json
(flow dev writes)        (PyQt5)       (flow scripts write)
```

**Zero coupling** — the GUI communicates with PD flow processes only through the filesystem.
Flow scripts write JSON files into timestamped run directories; the GUI scans and displays them.

## Configuration

Flow developers define steps, metrics, reports, and job columns in `flow_config.yaml`:

```yaml
flow_name: "Chip Design Flow"
steps:
  - name: init
  - name: floorplan
  - name: place
metrics:
  - key: WNS
    label: "WNS"
    format: ".3f"
    reports:
      - "reports/{version}/{step}/timing.rpt"
job_columns:
  - key: status
  - key: runtime

# Optional: script to run before each refresh
# refresh_command: "./pull_data.sh"

# Optional: custom command to open report files
# report_command: "gvim {file}"
```

Report paths support `{version}`, `{step}`, and `{run_dir}` template variables.
See [docs/flow_config_schema.md](docs/flow_config_schema.md) for the full schema reference.

## Run Data Format

Flow scripts write one JSON file per step into a timestamped directory under `runs/`:

```
runs/
└── 2026-05-19_1430_chip_A_golden/
    ├── run_info.json          # version metadata
    ├── init.json              # step data
    ├── floorplan.json
    └── ...
```

### JSON Format

```json
{
  "step": "place",
  "status": "SUCCESS",
  "metrics": { "WNS": -0.095, "TNS": -3.45 },
  "job": {
    "job_id": "lsf_batch_4521",
    "status": "SUCCESS",
    "memory_current_mb": 4096.0,
    "cpu_current_pct": 75.0,
    "runtime": "35m"
  }
}
```

- Missing step file → step is **not shown** in the table. This supports branched versions that only contain a subset of steps. To show a step as pending, write a JSON file with `"status": "PENDING"`.
- Overall version status derived from loaded step statuses: any FAIL → red, any RUNNING → blue, all SUCCESS → green

## GUI Layout

```
┌─────────────────     ─────────────────────────────────────────────┐
│ Toolbar: [Refresh] [Settings]         Font: [Consolas] [10]        │
├────────────     ┬─────────────────────────────────────────────────┤
│ VERSIONS        │  QScrollArea with stacked VersionTables         │
│                 │                                                 │
│ ● golden        │  ┌─ [−] Version: chip_A_golden ─ ✓ pass ──────┐│
│   STA running   │  │ Step   │ WNS    │ TNS   │ Status │ Runtime ││
│                 │  │ synth  │ -0.095 │ -3.45 │ ✓ pass │ 35m     ││
│ ● eco_v2        │  │ init   │   —    │  —    │ ✓ pass │ 8m      ││
│   STA pending   │  └─────────────────────────────────────────────┘│
│                 │                                                 │
│ ● exp.          │  ┌─ [−] Version: chip_A_eco_v2 ─ ✓ pass ──────┐│
│   route failed  │  │ ...                                        ││
│                 │  └─────────────────────────────────────────────┘│
├────────────     ┴─────────────────────────────────────────────────┤
│ Status: 4 runs | Latest: chip_A_in_progress                       │
└──────────────────────────────────────────────────────────────────┘
```

- **Left sidebar**: Version list with colored status dots, elided names, tooltips for full names
- **Right panel**: Stacked version tables, foldable with `[−]`/`[+]` buttons
- **Right-click** metric cells to open associated report files (configurable via `report_command` in Settings)

## CLI

```
python -m pdf_gui.main --config flow_config.yaml --runs runs/
```

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | `flow_config.yaml` | Path to YAML config |
| `--runs` | `runs` | Path to runs directory |

## Project Structure

```
pdf_gui/
├── models/
│   ├── run_data.py      # Version, Step, Job, enums
│   └── config.py        # FlowConfig + YAML parser
├── services/
│   ├── file_scanner.py  # Scans runs/ for timestamped dirs
│   └── data_loader.py   # JSON → model objects
├── widgets/
│   ├── toolbar.py         # Refresh, Settings, font controls
│   ├── metric_table.py    # Dynamic columns, right-click reports
│   ├── version_panel.py   # Foldable header + table
│   ├── sidebar.py         # Resizable list, dynamic name eliding
│   ├── settings_dialog.py # Refresh script + report command config
│   └── status_bar.py      # Run count + latest version
├── app.py               # MainWindow
└── main.py              # Entry point
```

## Running Tests

```bash
python -m pytest tests/ -v
```
