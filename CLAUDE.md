# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF GUI — a PyQt5 desktop application for monitoring VLSI physical design flows.
The GUI is flow-agnostic: flow developers describe their flow in a YAML config file,
and the GUI dynamically renders metric tables, charts, job status.

- **Stack**: Python 3.9, PyQt5

## Common Commands

```bash
# Install in dev mode
pip install -e .

# Install dependencies (Tsinghua mirror for China)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

## terminology and background
- **PD FLOW** Physical Design Flow for VLSI design, which consist of the steps like init, floorplan, place, cts, route, routeopt and etc, for different flow, the step name may vary.
- **Run Version** Each version represent a independent series of steps as mention before, the EDA tool may trigger different behaviour control by user plugin(PDF_GUI does not need to care about it)
- **Job** The steps are launch by certain task dispatch system, such as LSF or something else, the task is called job. A job has attributes like job ID, job status(RUNNING, PENDING, SUCCESS, FAIL), current/max/average memory/cpu usage and etc, which is also a important metric for physical backend designer.

## Initial GUI Layout

```
┌─────────────────     ─────────────────────────────────────────────┐
│ Toolbar: [Refresh]                   Font: [Consolas] [10]        │
├────────────     ┬─────────────────────────────────────────────────┤
│ VERSIONS        │  QScrollArea with stacked VersionTables         │
│                 │                                                 │
│ ● golden        │  ┌─ [−] Version: chip_A_golden ─ ✓ pass ─────┐  |
│   STA running   │  │ Step   │ WNS    │ TNS   │ Status │ Run Kl │  │
│                 │  │ synth  │ -0.095 │ -3.45 │ ✓ pass │ 35m    │  │
│ ● eco_v2        │  │ init   │   —    │  —    │ ✓ pass │ 8m     │  │
│   STA pending   │  │ ...    │        │       │        │        │  │
│                 │  │ STA    │ -0.005 │  0.0  │ ✓ pass │ 15m    │  │
│ ● exp.          │  └────────────────────────────────────────────┘ │
│   route failed  │                                                 │
│                 │  ┌─ [−] Version: chip_A_eco_v2 ─ ✓ pass ──────┐ │
│ ● wip           │  │ ...                                        │ │
│   place running │  └────────────────────────────────────────────┘ │
│                 │                                                 │
├────────────     ┴─────────────────────────────────────────────────┤
│ Status: 4 runs | Latest: chip_A_in_progress                       │
└──────────────────────────────────────────────────────────────┘
```

**Left sidebar**: Version list with colored status dots, version name, and latest step + status.
Long names are truncated with ellipsis; hovering shows the full name in a persistent popup.

**Right content**: All version tables stacked vertically in a scroll area.
Each version has a fold/unfold button `[−]`/`[+]` on the colored header bar.
Click a sidebar item to scroll to that version.

**Right-click** any metric cell to open associated report files (configured per-metric in YAML).

## Development and Deployment
- This project is developed in windows11.
- The real PD flow is in Linux system.
- PDF_GUI should work well in both windows11 and Linux.

## Architecture

- **Flow dev writes** `flow_config.yaml` → defines steps, metrics, reports, tasks, charts
- **Flow scripts write** JSON files into timestamped run directories → `runs/YYYY-MM-DD_HHMM_name/`
- **GUI reads** YAML config + scans run directories → displays in PyQt5 UI
- **Communication**: filesystem only (zero coupling between GUI and flow processes)

## Coding Philosophy
- **Every thing is configurable** What is shown in PDF_GUI is dynamic by config file. By manually or periodically refresh the config file, GUI dashboard is able to display real time data from PD flow.
- **Zero Coupling** PDF_GUI is independent with any physical design command line interface flow
- **User Friendiness** Design the GUI which is easy for data visualization, it should compatible to small screen(in development environment) and large screen(in deployment environment).
- **Complete API doc** The key of PDF_GUI is config file, and a detailed doc can guide flow developer to make smooth deployment.
- **Create realistic test case** Consider the situation when PDF_GUI is deployed in real PD flow environment.

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

