# Database Open Button — Implemented ✅

## Requirements (original)

1. The EDA tool database is usually opened by shell script wrapper or python script wrapper, not run EDA tool executable directly.
2. The database should be associated with version and step.
3. For certain step, it could have several databases.
4. The database button behaviour should also be configurable.
5. The situation is complex, because there are different EDA tools, different launching method.

## Implementation Summary

### Config model (`pdf_gui/models/config.py`)

- **`DatabaseConfig`** dataclass: `label` (display name) + `command` (launch template with `{version}`, `{step}`, `{run_dir}`, `{label}` placeholders)
- **`StepConfig.databases`**: `List[DatabaseConfig]` — per-step database entries
- **`FlowConfig.database_command`**: global fallback command used when a DB entry has no `command`

### UI (`pdf_gui/widgets/metric_table.py`)

- **"DB" column** appears when any step has databases (next to "Log" column)
- **QPushButton("DB")** per row for steps with databases configured
- Single database → direct subprocess launch
- Multiple databases → popup QMenu with database labels
- Command priority: per-DB `command` > global `database_command` > QSettings override

### Settings (`pdf_gui/widgets/settings_dialog.py`)

- "Database command" field in Settings dialog, persisted via QSettings

### YAML syntax

```yaml
step_groups:
  - name: APR
    steps:
      - name: place
        databases:
          - label: "ICC2 Layout"
            command: "icc2_dbm_open -design {version}_place"
          - label: "Verdi Debug"  
            command: "verdi -dbdir {run_dir}/{step}/verdi_db"
      - name: route
        databases:
          - label: "Route DB"
            # uses global database_command fallback

database_command: "eda_open {label} {version} {step}"
```

### Tests

- 14 tests in `tests/test_db_button.py` covering column presence, button rendering, header (plain+grouped), command resolution, QSettings override, subprocess launch, receipt file verification
- 3 config parsing tests in `tests/test_config.py`
- `tests/test_data/db_launcher.py` — simulator script (receipt file + popup window)
- Total test count: 66 (up from 49)

## UI Changes

### Table layout

A new **"DB" column** is added to the metric table when any step in the config has `databases` defined. Column order:

```
Step | Metric columns... | Job columns... | Log | DB
```

With grouped headers (`@` metrics), the DB header spans both rows like Log:

```
┌────────┬────── REG2REG ──────┬───── IO ─────┬──────────┬────────┬──────┐
│  Step  │  wns │  tns │  nvp  │ wns  │ tns   │ Density  │  Log   │  DB  │
├────────┼──────┼──────┼───────┼──────┼───────┼──────────┼────────┼──────┤
│  Init  │ —    │ —    │ —     │ —    │ —     │ 52.30    │ [Log]  │      │
│  Place │-0.050│-3.45 │ 12    │-0.01 │-0.50  │ 73.45    │ [Log]  │ [DB] │
│  CTS   │-0.030│-2.10 │ 8     │-0.02 │-0.30  │ 71.20    │ [Log]  │ [DB] │
│  Route │-0.015│-0.80 │ 3     │-0.01 │-0.15  │ 75.80    │ [Log]  │ [DB] │
└────────┴──────┴──────┴───────┴──────┴───────┴──────────┴────────┴──────┘
```

### Button behavior

- **QPushButton("DB")** with fixed height 40px per step row
- Step without databases → empty cell (no button)
- Single database → click launches command directly via `subprocess.Popen`
- Multiple databases → popup `QMenu` with database `label` as action names, positioned below the button:

```
                    ┌─────────────────────┐
                    │ ICC2 Layout         │
                    │ Verdi Debug         │
                    │ StarRC Extraction   │
                    └─────────────────────┘
```

### Settings dialog

New field added below "Picture command":

```
Database command: [custom_launcher {label} {version} {step} ]
```

Persisted via `QSettings("pdf_gui", "settings").value("database_command")`.

## Code Changes

### New files

| File | Lines | Purpose |
|------|-------|---------|
| `tests/test_data/db_launcher.py` | 73 | Simulator script: `--label`/`--version`/`--step` args → receipt file + popup window |
| `tests/test_db_button.py` | 354 | 14 tests: column, button, header, command resolution, QSettings, subprocess launch |

### Modified files

| File | ±Lines | Changes |
|------|--------|---------|
| `pdf_gui/models/config.py` | +21 | `DatabaseConfig` dataclass, `StepConfig.databases` field, `FlowConfig.database_command` field, YAML parsing in `load_config()` |
| `pdf_gui/widgets/metric_table.py` | +67 | `_has_databases` detection, DB column in constructor + grouped header, DB button in `_fill_data`, `_on_db_clicked` handler (single/multi menu), `_resolve_db_command` (template substitution), `_get_database_command` (QSettings override), `_launch_command` (subprocess.Popen), DB column width 45px |
| `pdf_gui/widgets/settings_dialog.py` | +10 | `KEY_DATABASE_COMMAND` constant, DB command QLineEdit, save/load via QSettings |
| `tests/test_data/flow_config.yaml` | +12 | Database entries on place/route/routeopt steps + global `database_command` |
| `tests/test_config.py` | +56 | `test_database_config_parsing`, `test_database_config_defaults`, `test_database_config_backward_compat` |

### Config model additions

```python
@dataclass
class DatabaseConfig:
    label: str           # display name in menu, e.g. "ICC2 Layout"
    command: str = ""    # launch template ({version}, {step}, {run_dir}, {label})

@dataclass  
class StepConfig:
    databases: List[DatabaseConfig] = field(default_factory=list)  # NEW

@dataclass
class FlowConfig:
    database_command: str = ""  # NEW — global fallback
```

### Key methods added to MetricTable

| Method | Purpose |
|--------|---------|
| `_on_db_clicked(row)` | Button click handler: resolves step config, single DB → direct launch, multi DB → QMenu popup |
| `_resolve_db_command(db, step_name)` | Template substitution: `{label}`, `{version}`, `{step}`, `{run_dir}` → resolved command string |
| `_get_database_command()` | QSettings override pattern: GUI setting > config YAML value |
| `_launch_command(cmd)` | `subprocess.Popen(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)` |

### Command resolution priority

```
per-DB command (DatabaseConfig.command)
  → global database_command (FlowConfig.database_command)
    → QSettings database_command (Settings dialog)
      → empty string (no-op, no crash)
```
