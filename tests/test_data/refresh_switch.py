"""Refresh toggle script — alternates between Suite 1 and Suite 2 test data.

Usage:
    python -m pdf_gui.main \
        --config tests/test_data/flow_config.yaml \
        --runs tests/test_data/runs \
        -r "python tests/test_data/refresh_switch.py"

Each Refresh click toggles between:
  Suite 1: 30 base versions
  Suite 2: 32 versions (2 new + some status/runtime modifications)
"""
import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, ".refresh_state")
GENERATOR = os.path.join(SCRIPT_DIR, "generate_test_data.py")


def main():
    suite = 1
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            suite = int(f.read().strip())

    next_suite = 2 if suite == 1 else 1
    time.sleep(3)  # Wait a moment to ensure the GUI has time to refresh before regenerating data
    subprocess.run(
        [sys.executable, GENERATOR, "--suite", str(next_suite)],
        check=True,
    )

    with open(STATE_FILE, "w") as f:
        f.write(str(next_suite))

    print(f"Switched to Suite {next_suite}")


if __name__ == "__main__":
    main()
