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

All configuration uses `step_groups` — each group defines its own steps, metrics, and tabs in the GUI.

```yaml
flow_name: "Chip Design Flow"
step_groups:
  - name: APR
    label: "APR"
    steps:
      - name: init
        logs:
          - "logs/{version}/{step}/run.log"
      - name: place
        databases:
          - label: "ICC2 Layout"
            command: "icc2_dbm_open -design {version}_place"
      - name: cts
        databases:
          - label: "CTS DB"
      - name: route
        databases:
          - label: "Route DB"
            command: "route_viewer {run_dir}/{step}"
    metrics:
      - key: WNS
        label: "WNS"
        format: ".3f"
        reports:
          - "reports/{version}/{step}/timing.rpt"
        step_reports:
          place:
            - "reports/{version}/place/place_opt0.rpt"
      - key: density
        label: "Density"
        pictures:
          - "img/{version}/{step}/density.png"
        step_pictures:
          place:
            - "img/{version}/place/density_place.png"
  - name: STA
    label: "STA"
    steps:
      - name: setup_scen_0
        logs:
          - "logs/{version}/{step}/run.log"
      - name: hold_scen_0
    metrics:
      - key: WNS
      - key: TNS
job_columns:
  - key: status
  - key: runtime

# Optional commands
# refresh_command: "./pull_data.sh"
# report_command: "gvim {file}"
# picture_command: "eog {file}"
# database_command: "eda_open {label} {version} {step}"
```

Each group appears as a tab in the GUI. Steps can be bare strings (`- place`) or objects with `name`/`logs`.
Report/log/picture paths support `{version}`, `{step}`, and `{run_dir}` template variables.

### Multi-level headers (`@` metric key grouping)

Metric keys with `@` produce grouped two-row table headers — the prefix (before `@`) becomes a parent label spanning its sub-columns:

```yaml
metrics:
  - key: REG2REG@wns       # "REG2REG" spans wns / tns / nvp
    label: "wns"
  - key: REG2REG@tns
    label: "tns"
  - key: REG2REG@nvp
    label: "nvp"
  - key: IO@wns             # "IO" spans wns / tns
    label: "wns"
  - key: IO@tns
    label: "tns"
  - key: density            # ungrouped — spans both rows
    label: "Density"
```

Renders as:

```
┌────────┬───── REG2REG ─────┬─────── IO ───────┬──────────┬───┐
│  Step  │ wns │ tns │ nvp   │ wns    │ tns     │ Density  │ … │
├────────┼─────┼─────┼───────┼────────┼─────────┼──────────┼───┤
│  init  │ …   │ …   │ …     │ …      │ …       │ …        │ … │
```

Same grouped header structure is preserved in CSV and Excel exports.

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
│ Toolbar: [Refresh] [Settings] [Export] [Sort] [Chart] Font: [...] │
├────────────     ┬─────────────────────────────────────────────────┤
│ VERSIONS        │ ┌─ APR ────┬─ STA ────┬─ PV ──────────────────┐│
│                 │ │ ─────────────────────────────────────────── ││
│ ● golden        │ │ ┌─ [−] Version: chip_A ─ ✓ SUCCESS ───────┐││
│   SUCCESS       │ │ │ Step   │ WNS    │ TNS   │ Status │Log│DB│││
│ ● eco_v2        │ │ │ init   │ -0.095 │ -3.45 │ ✓ pass │[L]│  │││
│   RUNNING       │ │ │ place  │ —      │ —     │ ✓ pass │[L]│[D]│││
│                 │ │ └──────────────────────────────────────────┘││
│ ● exp.          │ │ ┌─ [−] Version: chip_B ─ ⟳ RUNNING ───────┐││
│   FAIL          │ │ │ ...                                      │││
│                 │ └────────────────────────────────────────────┘││
│                 └───────────────────────────────────────────────┘│
├────────────     ┴─────────────────────────────────────────────────┤
│ SUCCESS:8 | RUNNING:11 | FAIL:6 | PENDING:5 | Sort: date | ...  │
└──────────────────────────────────────────────────────────────────┘
```

- **Left sidebar**: Version list filtered to active tab group, colored status dots (green/blue/red/orange) reflecting per-group status. Status text colored per status.
- **Right panel**: Tab widget with one tab per step group. Each tab shows version panels with only that group's steps and metrics. Foldable with `[−]`/`[+]` buttons.
- **Right-click** metric cells to open reports and pictures (separate sections in menu). Global + per-step report/picture paths. Configurable via `report_command`/`picture_command` in Settings.
- **Log button** per step row — opens step-specific log files (configured via `logs` on group steps).
- **DB button** per step row — launches EDA tool database viewers via configurable shell commands (configured via `databases` on group steps). Single database launches directly; multiple databases show a popup menu. Supports `{version}`, `{step}`, `{run_dir}`, `{label}` template variables.
- **Toolbar**: Refresh, Settings, Export (CSV/Excel per-group sheets), Sort (date or metric with group filter), Chart (cross-version Bar/Scatter/Histogram).

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
│   ├── metric_table.py     # Dynamic columns, reports/pictures, Log/DB btn
│   ├── version_panel.py    # Foldable colored header + table
│   ├── sidebar.py          # Resizable list, dynamic name eliding
│   ├── settings_dialog.py  # Refresh script, text/picture/DB commands
│   ├── export_dialog.py    # CSV/Excel export with version selection
│   ├── sort_dialog.py      # Sort by date or metric value
│   ├── chart_dialog.py     # Chart config: type, step, metrics, versions
│   ├── chart_window.py     # Matplotlib chart window with hover
│   └── status_bar.py       # Run count + latest version
├── theme.py              # Silicon Terminal dark theme (colors, QSS, fonts)
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

### Database button (EDA tool launcher)

Click **DB** in any step row to launch the EDA tool database viewer for that version+step. Configured via `databases` on steps in the YAML config. Each database entry has a `label` (display name) and optional `command` (launch template). Template variables `{version}`, `{step}`, `{run_dir}`, and `{label}` are substituted at runtime.

Single database → launches directly. Multiple databases → popup menu. If a database entry has no `command`, the global `database_command` is used as fallback. The Settings dialog provides a QSettings override.

```yaml
steps:
  - name: place
    databases:
      - label: "ICC2 Layout"
        command: "icc2_dbm_open -design {version}_place"
      - label: "Verdi Debug"
        command: "verdi -dbdir {run_dir}/{step}/verdi_db"
```

### Logging

Terminal output shows `[HH:MM:SS] INFO/WARNING/ERROR` messages for refresh lifecycle, config reloads, script failures, and file-not-found warnings. Set `PDF_GUI_DEBUG=1` to see DEBUG-level messages (e.g., skipped step files).
