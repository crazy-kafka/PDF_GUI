import csv
import os
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QMessageBox,
                             QPushButton, QVBoxLayout)

from pdf_gui.models.config import FlowConfig
from pdf_gui.models.run_data import StepStatus, Version
from pdf_gui.utils.log import get_logger

log = get_logger()


class ExportDialog(QDialog):
    def __init__(self, versions: List[Version], config: FlowConfig,
                 parent=None):
        super().__init__(parent)
        self._versions = versions
        self._config = config
        self.setWindowTitle("Export Versions")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)

        # version list with checkboxes
        self._list = QListWidget()
        for v in versions:
            item = QListWidgetItem(f"{v.name} ({v.status.value})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, v.name)
            self._list.addItem(item)
        layout.addWidget(self._list)

        # select / deselect all
        sel_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self._set_all(Qt.Checked))
        sel_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        sel_layout.addWidget(deselect_all_btn)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        # file path
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("File:"))
        self._path_edit = QLineEdit("export.csv")
        file_layout.addWidget(self._path_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # format
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Format:"))
        self._format_combo = QComboBox()
        self._format_combo.addItems(["CSV", "Excel (.xlsx)"])
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        fmt_layout.addWidget(self._format_combo)
        fmt_layout.addStretch()
        layout.addLayout(fmt_layout)

        # buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self._export_btn = QPushButton("Export")
        self._export_btn.clicked.connect(self._do_export)
        buttons.addButton(self._export_btn, QDialogButtonBox.AcceptRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_all(self, state: Qt.CheckState):
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(state)

    def _browse(self):
        fmt = "CSV (*.csv)" if self._format_combo.currentIndex() == 0 \
              else "Excel (*.xlsx)"
        path, _ = QFileDialog.getSaveFileName(self, "Export", "", fmt)
        if path:
            self._path_edit.setText(path)

    def _on_format_changed(self, idx: int):
        current = self._path_edit.text()
        if idx == 0 and current.endswith(".xlsx"):
            self._path_edit.setText(current[:-5] + ".csv")
        elif idx == 1 and current.endswith(".csv"):
            self._path_edit.setText(current[:-4] + ".xlsx")

    def _selected_versions(self) -> List[Version]:
        selected_names = set()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() == Qt.Checked:
                selected_names.add(item.data(Qt.UserRole))
        return [v for v in self._versions if v.name in selected_names]

    def _do_export(self):
        versions = self._selected_versions()
        if not versions:
            QMessageBox.warning(self, "Export", "No versions selected.")
            return

        path = self._path_edit.text().strip()
        if not path:
            return

        is_excel = self._format_combo.currentIndex() == 1
        if is_excel:
            self._write_excel(path, versions)
        else:
            self._write_csv(path, versions)

        log.info("Exported %d versions to %s", len(versions), path)
        self.accept()

    def _build_columns(self):
        return ["Step"] + [m.label for m in self._config.metrics] + \
               [c.label for c in self._config.job_columns]

    def _build_rows(self, version: Version):
        sc_map = {sc.name: sc for sc in self._config.steps}
        icon_map = {
            StepStatus.SUCCESS: self._config.icons.SUCCESS,
            StepStatus.FAIL: self._config.icons.FAIL,
            StepStatus.RUNNING: self._config.icons.RUNNING,
            StepStatus.PENDING: self._config.icons.PENDING,
        }
        rows = []
        for step in version.steps:
            sc = sc_map.get(step.name)
            row = [sc.label if sc else step.name]
            for mc in self._config.metrics:
                val = step.metrics.get(mc.key)
                row.append(format(val, mc.format) if val is not None else "—")
            for jc in self._config.job_columns:
                if step.job is None:
                    row.append("—")
                elif jc.key == "status":
                    icon = icon_map.get(step.status, "?")
                    row.append(f"{icon} {step.status.value}")
                else:
                    row.append(str(getattr(step.job, jc.key, "")))
            rows.append(row)
        return rows

    def _write_csv(self, path: str, versions: List[Version]):
        columns = self._build_columns()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            for i, v in enumerate(versions):
                if i > 0:
                    writer.writerow([])
                writer.writerow([f"# Version: {v.name} ({v.status.value})"])
                writer.writerow(columns)
                for row in self._build_rows(v):
                    writer.writerow(row)

    def _write_excel(self, path: str, versions: List[Version]):
        try:
            import openpyxl
        except ImportError:
            QMessageBox.warning(
                self, "Missing Dependency",
                "openpyxl is required for Excel export.\n"
                "Install it with: pip install openpyxl\n\n"
                "Falling back to CSV format.")
            self._write_csv(path, versions)
            return

        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        columns = self._build_columns()
        for v in versions:
            sheet_name = v.name[:31]
            ws = wb.create_sheet(title=sheet_name)
            ws.append(columns)
            for row in self._build_rows(v):
                ws.append(row)
        wb.save(path)
