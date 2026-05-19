from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout)

SETTINGS_ORG = "pdf_gui"
SETTINGS_APP = "settings"
KEY_REFRESH_COMMAND = "refresh_command"
KEY_REPORT_COMMAND = "report_command"


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)

        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Refresh script:"))

        cmd_layout = QHBoxLayout()
        self._cmd_edit = QLineEdit()
        self._cmd_edit.setText(self._settings.value(KEY_REFRESH_COMMAND, ""))
        self._cmd_edit.setPlaceholderText("/path/to/update_script.sh")
        cmd_layout.addWidget(self._cmd_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        cmd_layout.addWidget(browse_btn)

        layout.addLayout(cmd_layout)

        layout.addWidget(QLabel("Report command:"))

        rpt_layout = QHBoxLayout()
        self._rpt_edit = QLineEdit()
        self._rpt_edit.setText(self._settings.value(KEY_REPORT_COMMAND, ""))
        self._rpt_edit.setPlaceholderText("gvim {file}")
        rpt_layout.addWidget(self._rpt_edit)

        layout.addLayout(rpt_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Refresh Script", "",
            "Scripts (*.sh *.bat *.py *.cmd);;All Files (*)")
        if path:
            self._cmd_edit.setText(path)

    def _save_and_accept(self):
        self._settings.setValue(KEY_REFRESH_COMMAND, self._cmd_edit.text().strip())
        self._settings.setValue(KEY_REPORT_COMMAND, self._rpt_edit.text().strip())
        self.accept()
