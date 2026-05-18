import argparse
import os
import sys

from PyQt5.QtWidgets import QApplication

from pdf_gui.app import MainWindow


def main():
    parser = argparse.ArgumentParser(description="PDF GUI — PD Flow Monitor")
    parser.add_argument("--config", default="flow_config.yaml",
                        help="Path to flow_config.yaml")
    parser.add_argument("--runs", default="runs",
                        help="Path to runs directory")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("PDF_GUI")

    window = MainWindow(
        config_path=os.path.abspath(args.config),
        runs_dir=os.path.abspath(args.runs),
    )
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
