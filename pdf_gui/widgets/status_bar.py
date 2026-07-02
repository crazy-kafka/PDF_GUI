import getpass
from collections import Counter

from PyQt5.QtWidgets import QLabel


# Color map for status bar segments (functional, not user-configurable)
_STATUS_COLORS = {
    "SUCCESS": "#4CAF50",
    "RUNNING": "#2196F3",
    "FAIL": "#F44336",
    "PENDING": "#FF9800",
}


class StatusBar:
    def __init__(self, status_bar):
        self._bar = status_bar
        self._user = getpass.getuser()
        self._label = QLabel()
        self._bar.addPermanentWidget(self._label)

    def update(self, versions, sort_config=None, group_name: str = ""):
        """Show status counts for current group, sort method, and user name."""
        counts = Counter(v.status.value for v in versions)

        parts = []
        for label in ("SUCCESS", "RUNNING", "FAIL", "PENDING"):
            color = _STATUS_COLORS.get(label, "#8B949E")
            count = counts.get(label, 0)
            parts.append(
                f'<span style="color:{color};">{label}:{count}</span>')

        sort_info = "date"
        if sort_config and sort_config.get("rule") == "metric":
            sc = sort_config
            sort_info = f"{sc['metric_key']}/{sc['step_name']} ({'asc' if sc.get('ascending') else 'desc'})"

        prefix = f"{group_name} | " if group_name else ""
        text = prefix + " | ".join(parts) + f" | Sort: {sort_info} | User: {self._user}"
        self._label.setText(text)

    def update_text(self, text: str):
        self._label.setText(text)
