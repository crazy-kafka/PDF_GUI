# flow_config.yaml — Schema Reference

The YAML config file defines what the PDF_GUI dashboard displays. Flow developers
write this file once per flow; the GUI reads it and dynamically renders tables,
metrics, and job status columns.

Config is organized into **step groups** — each group becomes a tab in the GUI
with its own steps and metrics.

## Minimal Example

```yaml
flow_name: "My Flow"
step_groups:
  - name: APR
    steps:
      - synth
      - place
      - route
    metrics:
      - key: WNS
      - key: TNS
```

This produces one tab "APR" with columns `Step | WNS | TNS` and three rows.
All other fields use defaults.

## Full Schema

### Top-Level Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `flow_name` | string | no | `"PD Flow"` | Displayed in the window title |
| `step_groups` | list | **yes** | — | Step groups (tabs) |
| `job_columns` | list | no | `[]` | Job-info columns after metrics |
| `colors` | map | no | (see below) | Status color overrides |
| `icons` | map | no | (see below) | Status icon overrides |
| `default_font` | string | no | `"Consolas"` | Default monospace font |
| `default_font_size` | int | no | `10` | Font size (8–24) |
| `auto_refresh_seconds` | int | no | `0` | Auto-refresh interval (0 = manual) |
| `refresh_command` | string | no | `""` | Script run before refresh. Priority: CLI `-r` > Settings dialog > this YAML value |
| `report_command` | string | no | `""` | Command to open text files (reports, logs) |
| `picture_command` | string | no | `""` | Command to open picture files |
| `database_command` | string | no | `""` | Global fallback command for DB buttons. Supports `{label}`, `{version}`, `{step}`, `{run_dir}`. Priority: Settings dialog > this YAML value |

### `step_groups`

Each group defines a tab with its own steps, metrics, and optional label.

```yaml
step_groups:
  - name: APR              # required — group identifier
    label: "APR"           # optional — tab label (default: name)
    steps:                 # required — steps in this group
      - name: init         #   object form: with logs/label/databases
        logs:
          - "logs/{version}/{step}/run.log"
      - name: place
        databases:          #   per-step EDA database shortcuts
          - label: "ICC2 Layout"
            command: "icc2_dbm_open -design {version}_place"
          - label: "Verdi Debug"
            command: "verdi -dbdir {run_dir}/{step}/verdi_db"
      - cts                #   string form: bare step name
    metrics:               # optional — metrics for this group
      - key: WNS
        label: "WNS"
        format: ".3f"
        reports:
          - "reports/{version}/{step}/timing.rpt"
        step_reports:
          place:
            - "reports/{version}/place/place_opt0.rpt"
```

**Steps** can be:
- A string: `- place` (bare step name)
- An object: `- name: place; logs: [...]; databases: [...]` (with logs, databases, and optional label)

**Metrics** support the same fields as below (reports, pictures, step_reports, step_pictures).
Each group's metrics define the columns shown in that group's tab.

If any step in any group has `logs`, a "Log" column appears in the table.
Clicking the Log button opens the file (or shows a popup menu if multiple logs).

#### Database button (`databases` on steps)

Each step can have `databases` — shortcuts to launch EDA tool database viewers.
If any step in any group has `databases`, a **"DB" column** appears in the table.

```yaml
steps:
  - name: place
    databases:
      - label: "ICC2 Layout"            # required — display name
        command: "icc2_dbm_open -design {version}_place"  # optional launch template
      - label: "Verdi Debug"
        command: "verdi -dbdir {run_dir}/{step}/verdi_db"
      - label: "StarRC"
        # no command — uses global database_command fallback
```

Template variables for `command`:

| Variable | Expands to |
|----------|------------|
| `{version}` | Version name |
| `{step}` | Step name |
| `{run_dir}` | Full path to run directory |
| `{label}` | Database label (e.g., "ICC2 Layout") |

**Command resolution priority:**
1. Per-database `command` field
2. Global `database_command` from config
3. QSettings `database_command` from Settings dialog
4. If none configured: does nothing (no crash)

**Behavior:**
- Single database on a step → click launches directly via `subprocess.Popen`
- Multiple databases → popup `QMenu` with labels; click an item to launch
- No databases on a step → empty cell (no button)

### `metrics` (inside each group)

Each metric requires `key` and has optional `label`, `format`, `reports`, `pictures`,
`step_reports`, and `step_pictures`.

```yaml
metrics:
  - key: WNS                  # required — key in metrics dict within step JSON
    label: "WNS"              # optional — column header (default: key)
    format: ".3f"             # optional — Python float format spec (default: ".3f")
    reports:                  # optional — right-click: text report files
      - "reports/{version}/{step}/timing.rpt"
    pictures:                 # optional — right-click: image files
      - "img/{version}/{step}/density.png"
    step_reports:             # optional — step-specific additional reports
      place:
        - "rpt/{version}/place/place_opt0.rpt"
    step_pictures:            # optional — step-specific additional pictures
      place:
        - "img/{version}/place/extra.png"
```

Right-click context menu shows separate "Reports" and "Pictures" sections
when both are configured. Template variables apply to both.

`step_reports` and `step_pictures` are **added to** the global lists —
step-specific entries are appended, not replaced. The resolved list is
`reports + step_reports[step_name]`.

#### Multi-level headers (`@` metric key grouping)

When a metric `key` contains `@` (e.g., `REG2REG@wns`), the portion before `@`
becomes a **parent group label** spanning its sub-columns in a two-row table header.

```yaml
metrics:
  - key: REG2REG@wns         # "REG2REG" parent spans wns / tns / nvp
    label: "wns"
  - key: REG2REG@tns
    label: "tns"
  - key: REG2REG@nvp
    label: "nvp"
  - key: IO@wns               # "IO" parent spans wns / tns
    label: "wns"
  - key: IO@tns
    label: "tns"
  - key: density              # no @ — ungrouped, spans both header rows
    label: "Density"
```

This renders a two-row table header:

```
┌────────┬────── REG2REG ──────┬───────── IO ────────┬──────────┬───┐
│  Step  │  wns │  tns │  nvp  │  wns    │  tns     │ Density  │ … │
├────────┼──────┼──────┼───────┼─────────┼──────────┼──────────┼───┤
```

- **Row 0**: parent labels (`REG2REG`, `IO`) span their sub-columns via `setSpan`;
  ungrouped metrics span both rows.
- **Row 1**: sub-labels (`wns`, `tns`, `nvp`) for grouped metrics; empty for ungrouped.
- Consecutive metrics sharing the same `@` prefix are merged into one group.
- The same grouped header structure is preserved in CSV and Excel exports.
- A metric without `@` behaves normally — its label occupies both header rows.

Path templates support:

| Variable | Expands to |
|----------|------------|
| `{version}` | Version name (e.g., `chip_A_golden`) |
| `{step}` | Step name for the clicked cell (e.g., `cts`) |
| `{run_dir}` | Full path to the run directory |

Paths are resolved relative to the run directory (unless absolute).

### `job_columns`

Each job column requires `key` and has an optional `label`.

```yaml
job_columns:
  - key: status               # "status" is a special key — displays step status icon + text
    label: "Job Status"       # optional — column header (default: key.title())
  - key: runtime              # matches Job.runtime attribute
    label: "Wall Time"
```

Available job attribute keys: `job_id`, `status`, `memory_current_mb`, `memory_max_mb`,
`memory_avg_mb`, `cpu_current_pct`, `cpu_max_pct`, `cpu_avg_pct`, `runtime`.

### `colors` and `icons`

All optional. Defaults:

```yaml
colors:
  SUCCESS: "#4CAF50"   # green
  FAIL:    "#F44336"   # red
  RUNNING: "#2196F3"   # blue
  PENDING: "#FF9800"   # orange

icons:
  SUCCESS: "✓"
  FAIL:    "✗"
  RUNNING: "⟳"
  PENDING: "○"
```

---

## JSON Data Format (flow scripts → GUI)

Flow scripts write JSON files into timestamped run directories under `runs/`.
The directory naming convention is `YYYY-MM-DD_HHMM_version_name`.

### `run_info.json` (one per version directory)

```json
{
  "version": "chip_A_golden",
  "flow_name": "Chip Design Flow",
  "created_at": "2026-05-19T14:30:00"
}
```

- `version`: Display name for this run (required).
- `flow_name`: Informational only.
- `created_at`: ISO timestamp, informational only.

### `{step_name}.json` (one per step)

The filename must match a step `name` from the config (e.g., `place.json`).

```json
{
  "step": "place",
  "status": "SUCCESS",
  "metrics": {
    "WNS": -0.095,
    "TNS": -3.45,
    "max_cap": 0.023,
    "max_tran": 0.018
  },
  "job": {
    "job_id": "lsf_batch_4521",
    "status": "SUCCESS",
    "memory_current_mb": 4096.0,
    "memory_max_mb": 8192.0,
    "memory_avg_mb": 5120.0,
    "cpu_current_pct": 75.0,
    "cpu_max_pct": 98.0,
    "cpu_avg_pct": 82.0,
    "runtime": "35m"
  }
}
```

- `status`: One of `SUCCESS`, `RUNNING`, `FAIL`, `PENDING`.
- `metrics`: Dict of float values keyed by metric `key` from config. Missing keys or
  `null` values display as a dash (—).
- `job`: Optional job info. All fields are optional and default to `""` or `0`.
  - `runtime`: Free-form string displayed as-is.

### Missing Step Files

If a `{step_name}.json` file does not exist, the step is **not shown** in the version's
metric table. This supports branched versions that only contain a subset of steps
(e.g., a version branched from `cts` only has `cts.json`, `route.json`, etc.).

To display a step as PENDING (not yet started), write a JSON file with `"status": "PENDING"`:

```json
{
  "step": "route",
  "status": "PENDING",
  "metrics": {},
  "job": {}
}
```

### Overall Version Status

Derived from step statuses (checked in priority order):
- Any step `FAIL` → version `FAIL` (red)
- Any step `RUNNING` → version `RUNNING` (blue)
- All steps `SUCCESS` → version `SUCCESS` (green)
- Any step `PENDING` → version `PENDING` (orange)
- No steps → version `PENDING` (orange)

---

## Directory Layout

```
project/
├── flow_config.yaml          # flow developer writes this
├── runs/                     # flow scripts write into this
│   ├── 2026-05-19_1430_chip_A_golden/
│   │   ├── run_info.json
│   │   ├── init.json
│   │   ├── floorplan.json
│   │   ├── place.json
│   │   └── ...
│   ├── 2026-05-19_1530_chip_A_eco_v2/
│   │   └── ...
│   └── ...
└── reports/                  # optional, referenced by metric.reports paths
    └── timing.rpt
```
