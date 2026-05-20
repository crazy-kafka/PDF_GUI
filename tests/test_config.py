import tempfile
import os

from pdf_gui.models.config import load_config


def test_load_minimal_config():
    yaml_content = """
flow_name: "Test Flow"
steps:
  - name: synth
  - name: place
metrics:
  - key: WNS
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        config = load_config(path)
        assert config.flow_name == "Test Flow"
        assert len(config.steps) == 2
        assert config.steps[0].name == "synth"
        assert config.steps[0].label == "Synth"  # default: name.title()
        assert config.steps[1].name == "place"
        assert config.steps[1].label == "Place"
        assert len(config.metrics) == 1
        assert config.metrics[0].key == "WNS"
        assert config.metrics[0].label == "WNS"
        assert config.metrics[0].format == ".3f"
        assert config.metrics[0].reports == []
        assert config.colors.SUCCESS == "#4CAF50"
        assert config.default_font == "Consolas"
        assert config.default_font_size == 10
        assert config.auto_refresh_seconds == 0
    finally:
        os.unlink(path)


def test_load_full_config():
    yaml_content = """
flow_name: "Full Flow"
steps:
  - name: init
    label: "Initialize"
  - name: place
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
        assert config.steps[0].label == "Initialize"
        assert config.metrics[0].label == "Worst NS"
        assert config.metrics[0].format == ".4f"
        assert config.metrics[0].reports == ["reports/timing.rpt"]
        assert len(config.job_columns) == 2
        assert config.job_columns[0].key == "status"
        assert config.job_columns[0].label == "Status"
        assert config.job_columns[1].key == "runtime"
        assert config.job_columns[1].label == "Runtime"  # default for "runtime"
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
steps:
  - name: init
    logs:
      - "logs/{version}/{step}/run.log"
  - name: place
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
        assert config.steps[0].logs == ["logs/{version}/{step}/run.log"]
        assert config.steps[1].logs == []
        assert config.metrics[0].pictures == []
        assert config.metrics[1].pictures == [
            "img/density.png", "img/density_hist.png"]
    finally:
        os.unlink(path)


def test_job_column_default_label():
    """Job column labels should default to key.title() replacing _ with space."""
    yaml_content = """
flow_name: "Test"
steps: []
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
