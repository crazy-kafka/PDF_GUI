import os
import re
from typing import List

RUN_DIR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}_.+$")


def scan_runs(runs_dir: str) -> List[str]:
    """Return sorted list of run directory paths (most recent first)."""
    if not os.path.isdir(runs_dir):
        return []

    entries = []
    for name in os.listdir(runs_dir):
        full = os.path.join(runs_dir, name)
        if os.path.isdir(full) and RUN_DIR_PATTERN.match(name):
            entries.append(full)

    entries.sort(reverse=True)
    return entries
