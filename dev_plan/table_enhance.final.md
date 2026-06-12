# Multi-Level Table Header via `@` Metric Key — Final Plan

## Config API (zero model changes)

Use `@` as a group separator in metric keys:

```yaml
metrics:
  - key: density
    label: "Density"
    format: ".2f"
  - key: REG2REG@wns
    label: "wns"
    format: ".3f"
  - key: REG2REG@tns
    label: "tns"
    format: ".3f"
  - key: REG2REG@nvp
    label: "nvp"
    format: ".0f"
  - key: IO@wns
    label: "wns"
  - key: IO@tns
    label: "tns"
  - key: IO@nvp
    label: "nvp"
```

- `REG2REG@wns` → group=`REG2REG`, sub-label=`wns`, data key=`REG2REG@wns`
- Consecutive metrics sharing the same `@`-prefix are grouped together
- No `@` → flat metric (current behavior, unchanged)

---

## 1. Table Layout (GUI)

```
        ┌──────┬─────────────────┬─────────────────┬─────────┬────────────┬─────────┐
Row 0   │ Step │    REG2REG      │       IO        │ Density │ Job Status │ Runtime │
Row 1   │      │ wns │ tns │ nvp │ wns │ tns │ nvp │         │            │         │
        ├──────┼─────┼─────┼─────┼─────┼─────┼─────┼─────────┼────────────┼─────────┤
Row 2   │ init │ 0.1 │ 10.0│ 100 │ 0.1 │ 10.0│ 100 │  56%    │ ✓ SUCCESS  │ 8m      │
        └──────┴─────┴─────┴─────┴─────┴─────┴─────┴─────────┴────────────┴─────────┘
```

- Rows 0-1: regular table rows styled as headers (dark bg `#37474F`, white bold)
- QHeaderView hidden (`setVisible(False)`)
- Row 0: group labels span their sub-columns via `setSpan(0, start_col, 1, n_sub_cols)`
- Ungrouped metrics span 2 rows via `setSpan(0, col, 2, 1)`
- Data rows start at offset 2
- Height calculation includes header rows
- `resize_for_font()` includes header row heights

## 2. Export Behavior (CSV & XLSX)

Export mirrors the same grouped layout:

### CSV
```
Step,REG2REG,,,IO,,,Density,Job Status,Runtime
,wns,tns,nvp,wns,tns,nvp,,,
init,0.1,10.0,100,0.1,10.0,100,56%,✓ SUCCESS,8m
```

- Row 0: parent group labels (empty for sub-columns, merged via `""`)
- Row 1: sub-labels for grouped metrics, empty for ungrouped
- Row 2+: data

### XLSX
Same two-row header with merged cells (`ws.merge_cells` for parent group labels), styled like the GUI header (dark bg, white bold). One sheet per group (current behavior).

**Implementation**: extract a `_build_header_layout(config, group)` shared utility that returns column layout info `[(parent_label, sub_label, col_span_info), ...]`. Both `MetricTable` and `ExportDialog` call it to build consistent headers.

### Changes in export_dialog.py

- `_write_csv`: write two header rows when groups detected
- `_write_excel_sheet`: merge cells for parent group labels, two-row header

---

## 3. Code Changes

### `metric_table.py`

- **`__init__`**: parse `@` keys, detect groups, build column layout
- **Header rendering**: two-row header with spans, styled cells
- **Data offset**: `data_row_offset = 2 if has_groups else 0`
- **Height + resize_for_font**: include header rows

```python
def _parse_groups(self, eff_metrics):
    """Parse @-prefixed metric keys into groups."""
    groups = OrderedDict()  # prefix → (start_col, sub_labels, metric_configs)
    has_groups = False
    col = 1  # col 0 = Step
    for m in eff_metrics:
        if "@" in m.key:
            has_groups = True
            prefix, sub = m.key.split("@", 1)
            if prefix not in groups:
                groups[prefix] = (col, [], [])
            groups[prefix][1].append(m.label)
            groups[prefix][2].append(m)
        col += 1
    return groups, has_groups
```

### `export_dialog.py`

- `_build_header_layout(config, group)` → shared with MetricTable for column layout
- `_write_csv`: two header rows
- `_write_excel_sheet`: merge cells for parent labels

### No changes

- **Sort dialog**: full key `REG2REG@wns` shown as-is ✓
- **Chart dialog**: same ✓
- **Data loader**: `REG2REG@wns` is the metric key in step JSON ✓

---

## 4. Test Plan

### Unit tests (`tests/test_run_data.py` — 2 new)

| Test | What |
|------|------|
| `test_metric_table_detects_groups` | Table with `@` metrics → `has_groups=True`, correct group mapping |
| `test_metric_table_no_groups` | Table without `@` → `has_groups=False`, single-row header |

### Export tests (`tests/test_export_dialog.py` — 2 new)

| Test | What |
|------|------|
| `test_csv_grouped_header` | CSV has two header rows with group labels |
| `test_xlsx_grouped_header` | XLSX has merged cells for parent group labels |

### GUI interactive testing (manual)

| Scenario | Steps | Expected |
|----------|-------|----------|
| Launch with `@` metrics | `python -m pdf_gui.main --config tests/test_data/flow_config.yaml --runs tests/test_data/runs` | Two-row header: parent labels spanning sub-columns |
| Right-click grouped metric | Right-click `wns` under REG2REG | Context menu shows correct report paths |
| Sort by grouped metric | Click Sort → select REG2REG@wns → Apply | Versions sorted by that metric |
| Chart grouped metric | Click Chart → select REG2REG@wns | Bar chart renders correctly |
| Export CSV grouped | Click Export → CSV → open | Two header rows matching table layout |
| Export XLSX grouped | Click Export → XLSX → open | Merged parent labels, same style |
| Tab switch with groups | Switch APR→STA tab | Grouped layout preserved per tab |
| Font resize | Increase font size to 24 | Header rows resize correctly |
| Launch without `@` metrics | Use config with flat metrics only | Single-row header (backward compat) |
| Step with missing grouped metric | Version without REG2REG@wns | Dash shown in cell |

---

## 5. Documentation

- `docs/flow_config_schema.md`: Document `@` metric grouping under `metrics` section
- Test config: Add `@` grouped metrics in `tests/test_data/flow_config.yaml`

---

## Files Modified (final)

| File | Change |
|------|--------|
| `pdf_gui/widgets/metric_table.py` | Parse `@` keys, two-row header, data offset |
| `pdf_gui/widgets/export_dialog.py` | Two-row header in CSV/XLSX |
| `tests/test_data/flow_config.yaml` | Add `@` grouped metrics |
| `tests/test_run_data.py` | +2 tests: group detection, no-group fallback |
| `tests/test_export_dialog.py` | +2 tests: CSV/XLSX grouped headers |
| `docs/flow_config_schema.md` | Document `@` grouping |

## Verification

1. `python -m pytest tests/ -v` — 50 tests pass (46 existing + 4 new)
2. Run all 10 GUI interactive test scenarios above
