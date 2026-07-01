import tempfile
import os

from pdf_gui.models.config import load_config


def test_load_minimal_config():
    yaml_content = """
flow_name: "Test Flow"
step_groups:
  - name: All
    steps:
      - synth
      - place
    metrics:
      - key: WNS
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        assert config.flow_name == "Test Flow"
        g = config.step_groups[0]
        assert g.name == "All"
        assert [s.name for s in g.steps] == ["synth", "place"]
        assert len(g.metrics) == 1
        assert g.metrics[0].key == "WNS"
        assert g.metrics[0].label == "WNS"
        assert g.metrics[0].format == ".3f"
        assert g.metrics[0].reports == []
        assert config.colors.SUCCESS == "#4CAF50"
        assert config.default_font == "Consolas"
        assert config.default_font_size == 10
        assert config.auto_refresh_seconds == 0
    finally:
        os.unlink(path)


def test_load_full_config():
    yaml_content = """
flow_name: "Full Flow"
step_groups:
  - name: All
    steps:
      - init
      - place
    metrics:
      - key: WNS
        label: "Worst NS"
        format: ".4f"
        reports:
          - "reports/timing.rpt"
job_columns:
  - key: status
    label: "Status"
  - key: runtime
colors:
  SUCCESS: "#00FF00"
  FAIL: "#FF0000"
  RUNNING: "#0000FF"
  PENDING: "#888888"
icons:
  SUCCESS: "OK"
  FAIL: "XX"
  RUNNING: ">>"
  PENDING: ".."
default_font: "Courier"
default_font_size: 12
auto_refresh_seconds: 30
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        assert config.flow_name == "Full Flow"
        g = config.step_groups[0]
        assert [s.name for s in g.steps] == ["init", "place"]
        assert g.metrics[0].label == "Worst NS"
        assert g.metrics[0].format == ".4f"
        assert g.metrics[0].reports == ["reports/timing.rpt"]
        assert len(config.job_columns) == 2
        assert config.job_columns[0].key == "status"
        assert config.job_columns[0].label == "Status"
        assert config.job_columns[1].key == "runtime"
        assert config.job_columns[1].label == "Runtime"
        assert config.colors.SUCCESS == "#00FF00"
        assert config.colors.FAIL == "#FF0000"
        assert config.icons.SUCCESS == "OK"
        assert config.default_font == "Courier"
        assert config.default_font_size == 12
        assert config.auto_refresh_seconds == 30
    finally:
        os.unlink(path)


def test_load_logs_and_pictures():
    """logs in steps and pictures in metrics should be parsed."""
    yaml_content = """
flow_name: "Test"
step_groups:
  - name: All
    steps:
      - name: init
        logs:
          - "logs/{version}/{step}/run.log"
      - place
    metrics:
      - key: WNS
        reports:
          - "rpt/timing.rpt"
      - key: density
        reports:
          - "rpt/density.rpt"
        pictures:
          - "img/density.png"
          - "img/density_hist.png"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        g = config.step_groups[0]
        assert [s.name for s in g.steps] == ["init", "place"]
        assert g.metrics[0].pictures == []
        assert g.metrics[1].pictures == [
            "img/density.png", "img/density_hist.png"]
    finally:
        os.unlink(path)


def test_step_reports_parsing():
    """step_reports and step_pictures are parsed into dicts."""
    yaml_content = """
flow_name: "Test"
step_groups:
  - name: All
    steps:
      - init
      - place
    metrics:
      - key: WNS
        reports:
          - "rpt/timing.rpt"
        step_reports:
          init:
            - "rpt/init_extra.rpt"
          place:
            - "rpt/place_opt0.rpt"
            - "rpt/place_opt1.rpt"
        step_pictures:
          place:
            - "img/place_density.png"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        mc = config.step_groups[0].metrics[0]
        assert mc.reports == ["rpt/timing.rpt"]
        assert mc.step_reports == {
            "init": ["rpt/init_extra.rpt"],
            "place": ["rpt/place_opt0.rpt", "rpt/place_opt1.rpt"],
        }
        assert mc.step_pictures == {"place": ["img/place_density.png"]}
    finally:
        os.unlink(path)


def test_step_reports_backward_compat():
    """Metrics without step_reports still work — empty dict."""
    yaml_content = """
flow_name: "Test"
step_groups:
  - name: All
    steps:
      - init
    metrics:
      - key: WNS
        reports:
          - "rpt/timing.rpt"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        mc = config.step_groups[0].metrics[0]
        assert mc.reports == ["rpt/timing.rpt"]
        assert mc.step_reports == {}
        assert mc.step_pictures == {}
    finally:
        os.unlink(path)


def test_database_config_parsing():
    """databases on steps parsed into DatabaseConfig list."""
    yaml_content = """
flow_name: "Test"
step_groups:
  - name: APR
    steps:
      - name: place
        databases:
          - label: "ICC2 Layout"
            command: "icc2_open -db {version}/{step}"
          - label: "Verdi Debug"
            command: "verdi -db {run_dir}/{step}"
      - name: cts
    metrics:
      - key: WNS
database_command: "default_db_open {label}"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        g = config.step_groups[0]
        place_step = [s for s in g.steps if s.name == "place"][0]
        cts_step = [s for s in g.steps if s.name == "cts"][0]
        assert len(place_step.databases) == 2
        assert place_step.databases[0].label == "ICC2 Layout"
        assert place_step.databases[0].command == "icc2_open -db {version}/{step}"
        assert place_step.databases[1].label == "Verdi Debug"
        assert place_step.databases[1].command == "verdi -db {run_dir}/{step}"
        assert cts_step.databases == []
        assert config.database_command == "default_db_open {label}"
    finally:
        os.unlink(path)


def test_database_config_defaults():
    """Step without databases gets empty list; DB without command gets ''."""
    yaml_content = """
flow_name: "Test"
step_groups:
  - name: APR
    steps:
      - name: init
    metrics:
      - key: WNS
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        step = config.step_groups[0].steps[0]
        assert step.databases == []
        assert config.database_command == ""
    finally:
        os.unlink(path)


def test_database_config_backward_compat():
    """Config without databases key loads without error."""
    yaml_content = """
flow_name: "Test"
step_groups:
  - name: All
    steps:
      - init
      - place
    metrics:
      - key: WNS
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        g = config.step_groups[0]
        for s in g.steps:
            assert s.databases == []
    finally:
        os.unlink(path)


def test_job_column_default_label():
    """Job column labels should default to key.title() replacing _ with space."""
    yaml_content = """
flow_name: "Test"
step_groups:
  - name: All
job_columns:
  - key: memory_current_mb
  - key: cpu_avg_pct
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        assert config.job_columns[0].label == "Memory Current Mb"
        assert config.job_columns[1].label == "Cpu Avg Pct"
    finally:
        os.unlink(path)
