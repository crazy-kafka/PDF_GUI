import getpass
from collections import Counter


class StatusBar:
    def __init__(self, status_bar):
        self._bar = status_bar
        self._user = getpass.getuser()

    def update(self, versions, sort_config=None):
        """Show status counts, sort method, and user name."""
        counts = Counter(v.status.value for v in versions)
        parts = [f"SUCCESS:{counts.get('SUCCESS', 0)}",
                 f"RUNNING:{counts.get('RUNNING', 0)}",
                 f"FAIL:{counts.get('FAIL', 0)}",
                 f"PENDING:{counts.get('PENDING', 0)}"]

        sort_info = "date"
        if sort_config and sort_config.get("rule") == "metric":
            sc = sort_config
            sort_info = f"{sc['metric_key']}/{sc['step_name']} ({'asc' if sc.get('ascending') else 'desc'})"

        text = " | ".join(parts) + f" | Sort: {sort_info} | User: {self._user}"
        self._bar.showMessage(text)

    def update_text(self, text: str):
        self._bar.showMessage(text)
