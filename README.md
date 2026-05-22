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
    logs:
      - "logs/{version}/{step}/run.log"
  - name: place
metrics:
  - key: WNS
    label: "WNS"
    format: ".3f"
    reports:
      - "reports/{version}/{step}/timing.rpt"
  - key: density
    label: "Density"
    reports:
      - "rpt/{version}/{step}/density.rpt"
    pictures:
      - "img/{version}/{step}/density.png"
job_columns:
  - key: status
  - key: runtime

# Optional: script to run before each refresh
# refresh_command: "./pull_data.sh"

# Optional: custom commands to open files
# report_command: "gvim {file}"        # text files (reports, logs)
# picture_command: "eog {file}"        # picture files
```

Report/log/picture paths support `{version}`, `{step}`, and `{run_dir}` template variables.
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

- Missing step file → step is **not shown**. Supports branched versions (subset of steps). Write `"status": "PENDING"` JSON to show pending.
- Overall version status (checked in priority order): any FAIL → red, any RUNNING → blue, all SUCCESS → green, last step PENDING + second-last SUCCESS → orange

## GUI Layout

```
┌─────────────────     ─────────────────────────────────────────────┐
│ Toolbar: [Refresh] [Settings] [Export] [Sort]  Font: [Consolas] [10] │
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

- **Left sidebar**: Version list with colored status dots (green/blue/red/orange), elided names, tooltips for full names. Status text colored per status.
- **Right panel**: Stacked version tables, foldable with `[−]`/`[+]` buttons. Metric table columns sized to content. Colored job status text.
- **Right-click** metric cells to open reports and pictures (separate sections in menu). Configurable via `report_command`/`picture_command` in Settings.
- **Log button** per step row — opens step-specific log files.
- **Toolbar**: Refresh, Settings (refresh script, text/picture open commands), Export (CSV/Excel), Sort (date or metric-based), Chart (cross-version visualization).

## CLI

```
python -m pdf_gui.main --config flow_config.yaml --runs runs/
```

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | `flow_config.yaml` | Path to YAML config |
| `--runs` | `runs` | Path to runs directory |
| `-r`, `--refresh_command` | (none) | Override refresh script (priority: CLI > Settings > config) |

## Project Structure

```
pdf_gui/
├── models/
│   ├── run_data.py      # Version, Step, Job, enums
│   └── config.py        # FlowConfig + YAML parser
├── services/
│   ├── file_scanner.py      # Scans runs/ for timestamped dirs
│   ├── data_loader.py       # JSON → model objects
│   └── dataframe_builder.py # Versions → pandas DataFrame
├── utils/
│   └── log.py              # Centralized logging (INFO/WARNING/ERROR)
├── widgets/
│   ├── toolbar.py          # Refresh, Settings, Export, Sort, Chart, font
│   ├── metric_table.py     # Dynamic columns, reports/pictures, Log btn
│   ├── version_panel.py    # Foldable colored header + table
│   ├── sidebar.py          # Resizable list, dynamic name eliding
│   ├── settings_dialog.py  # Refresh script, text/picture commands
│   ├── export_dialog.py    # CSV/Excel export with version selection
│   ├── sort_dialog.py      # Sort by date or metric value
│   ├── chart_dialog.py     # Chart config: type, step, metrics, versions
│   ├── chart_window.py     # Matplotlib chart window with hover
│   └── status_bar.py       # Run count + latest version
├── app.py                # MainWindow
└── main.py              # Entry point (+ -r flag)
```

## Running Tests

```bash
python -m pytest tests/ -v
```

### Refresh toggle test

Simulates real PD flow updates (new versions, status changes) alternating each refresh:

```bash
python -m pdf_gui.main \
    --config tests/test_data/flow_config.yaml \
    --runs tests/test_data/runs \
    -r "python tests/test_data/refresh_switch.py"
```

Click Refresh repeatedly — version count toggles between 30 and 32, with step statuses and runtimes changing.

### Sort versions

Click **Sort** in the toolbar to reorder versions by date (default) or by a metric value in a specific step (ascending/descending). Missing data can be pushed to top, bottom, or excluded. Sort rule persists across refreshes — new versions automatically land in the correct position.

### Export versions

Click **Export** in the toolbar, select which versions to include (all checked by default), choose CSV or Excel format, pick a file path, and export. Excel uses a single sheet with merged version column, styled headers, and auto-fitted column widths. Requires `openpyxl` (`pip install openpyxl`).

### Chart versions (cross-version visualization)

Click **Chart** in the toolbar to visualize metrics across versions. Select chart type, step, metrics, and versions to include.

| Chart type | Description |
|------------|-------------|
| Line/Bar | One metric across versions, bars colored by status. Hover for full version name. |
| Scatter | Two metrics plotted against each other (e.g., WNS vs TNS). Each point = one version. |
| Histogram | Distribution of one metric across versions with mean/median lines. |

DataModel: versions are converted to a pandas DataFrame (`pdf_gui/services/dataframe_builder.py`) once per refresh — used as the data source for all charts. Requires `matplotlib`, `pandas`.

### Logging

Terminal output shows `[HH:MM:SS] INFO/WARNING/ERROR` messages for refresh lifecycle, config reloads, script failures, and file-not-found warnings. Set `PDF_GUI_DEBUG=1` to see DEBUG-level messages (e.g., skipped step files).
