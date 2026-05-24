import argparse
import os
import sys

from PyQt5.QtWidgets import QApplication

from pdf_gui.app import MainWindow
from pdf_gui.utils.log import get_logger

log = get_logger()


def main():
    parser = argparse.ArgumentParser(description="PDF GUI — PD Flow Monitor")
    parser.add_argument("--config", default="flow_config.yaml",
                        help="Path to flow_config.yaml")
    parser.add_argument("--runs", default="runs",
                        help="Path to runs directory")
    parser.add_argument("-r", "--refresh_command", default=None,
                        help="Override refresh script (takes priority over config)")
    args = parser.parse_args()

    config_path = os.path.abspath(args.config)
    runs_dir = os.path.abspath(args.runs)
    log.info("Starting PDF_GUI — config=%s, runs=%s", config_path, runs_dir)
    if args.refresh_command:
        log.info("Refresh command from CLI: %s", args.refresh_command)

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("PDF_GUI")

        window = MainWindow(
            config_path=config_path,
            runs_dir=runs_dir,
            cli_refresh_command=args.refresh_command,
        )
        window.show()

        sys.exit(app.exec_())
    except Exception as e:
        log.error("Failed to start GUI: %s", e)
        raise


if __name__ == "__main__":
    main()
