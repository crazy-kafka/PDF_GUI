"""DB launcher simulator for testing the database open button feature.

This is a standalone script (no imports from pdf_gui). It is invoked via
subprocess by the DB button click handler during tests, simulating how
a real EDA tool launcher wrapper would be called.

Behavior:
  - Accepts --label, --version, --step command-line arguments
  - Writes a receipt file for automated test assertions
  - Optionally pops up a brief PyQt5 window (visible during manual testing)
  - Auto-closes after 1.5 seconds
"""

import argparse
import os
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description="DB Launcher Simulator")
    parser.add_argument("--label", default="unknown",
                        help="Database label (e.g., 'ICC2 Layout')")
    parser.add_argument("--version", default="unknown",
                        help="Version name (e.g., 'chip_A_golden')")
    parser.add_argument("--step", default="unknown",
                        help="Step name (e.g., 'place')")
    parser.add_argument("--no-gui", action="store_true",
                        help="Skip popup window (headless test mode)")
    args = parser.parse_args()

    # ── Write receipt file for automated test assertions ─────────
    receipt_dir = os.environ.get("DB_RECEIPT_DIR", tempfile.gettempdir())
    receipt_path = os.path.join(
        receipt_dir, f"db_open_receipt_{int(time.time() * 1000)}.txt")
    with open(receipt_path, "w", encoding="utf-8") as f:
        f.write(f"{args.label}|{args.version}|{args.step}")
    print(f"[db_launcher] receipt → {receipt_path}")

    # ── Pop up a brief window (proves subprocess was launched) ──
    if not args.no_gui:
        try:
            from PyQt5.QtCore import QTimer
            from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
        except ImportError:
            print("[db_launcher] PyQt5 not available, skipping GUI popup")
            return

        app = QApplication(sys.argv)
        win = QWidget()
        win.setWindowTitle("DB Launcher")
        win.setMinimumSize(350, 120)
        layout = QVBoxLayout(win)
        label = QLabel(
            f"Opened: {args.label}\n"
            f"Version: {args.version}\n"
            f"Step: {args.step}"
        )
        label.setStyleSheet(
            "font-size: 14px; padding: 16px; "
            "background-color: #161B22; color: #E6EDF3;"
        )
        layout.addWidget(label)
        win.show()
        QTimer.singleShot(1500, app.quit)
        app.exec_()


if __name__ == "__main__":
    main()
