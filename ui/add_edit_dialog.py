from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence
from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.models import DialogDraft, LauncherItem, LauncherType, RunMode, ScriptType
from core.windows_shortcuts import supported_target_file_dialog_filter, supported_target_summary


class AddEditLauncherDialog(QDialog):
    def __init__(
        self,
        *,
        available_actions: Sequence[str],
        item: LauncherItem | None = None,
        draft: DialogDraft | None = None,
        preset_type: LauncherType | None = None,
        preset_target: str | None = None,
        type_locked: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._editing_item = item
        self._available_actions = list(available_actions)
        self._result_item: LauncherItem | None = None
        self._draft = draft or DialogDraft()
        self._last_type = item.type if item else preset_type or LauncherType.URL
        self._type_locked = type_locked

        self.setWindowTitle("Edit Orbit Panel Card" if item else "Add Orbit Panel Card")
        self.setModal(True)
        self.setMinimumWidth(580)

        self._build_ui()
        self._populate(item=item, draft=draft, preset_type=preset_type, preset_target=preset_target)
        self._apply_type_state()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 22, 22, 22)
        root_layout.setSpacing(18)

        title = QLabel("Orbit Panel Card")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Create a URL or EXE entry and choose whether Run opens the target, runs the script, or both.")
        subtitle.setObjectName("SectionSubtitle")
        subtitle.setWordWrap(True)

        form = QFormLayout()
        form.setSpacing(14)
        form.setVerticalSpacing(14)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Card title")

        self.type_combo = QComboBox()
        self.type_combo.addItem("URL", LauncherType.URL.value)
        self.type_combo.addItem("EXE", LauncherType.EXE.value)
        self.type_combo.currentIndexChanged.connect(self._apply_type_state)
        self.type_combo.setEnabled(not self._type_locked)

        self.target_label = QLabel("Target")
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("https://example.com")

        self.target_browse_button = QPushButton("Browse")
        self.target_browse_button.clicked.connect(self._browse_target)

        target_row = QWidget()
        target_layout = QHBoxLayout(target_row)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(10)
        target_layout.addWidget(self.target_input, 1)
        target_layout.addWidget(self.target_browse_button, 0)

        self.script_type_combo = QComboBox()
        self.script_type_combo.addItem("None", ScriptType.NONE.value)
        self.script_type_combo.addItem("Built-in Action", ScriptType.BUILT_IN_ACTION.value)
        self.script_type_combo.addItem("Python File", ScriptType.PYTHON_FILE.value)
        self.script_type_combo.currentIndexChanged.connect(self._apply_type_state)

        self.action_script_combo = QComboBox()
        self.action_script_combo.setEditable(True)
        self.action_script_combo.addItems(self._available_actions)
        if self.action_script_combo.lineEdit() is not None:
            self.action_script_combo.lineEdit().setPlaceholderText(
                "For example: browser_login_placeholder_action"
            )

        self.python_script_input = QLineEdit()
        self.python_script_input.setPlaceholderText(r"scripts/examples/browser_login_stub.py")
        self.python_script_browse_button = QPushButton("Browse")
        self.python_script_browse_button.clicked.connect(self._browse_python_script)

        python_row = QWidget()
        python_layout = QHBoxLayout(python_row)
        python_layout.setContentsMargins(0, 0, 0, 0)
        python_layout.setSpacing(10)
        python_layout.addWidget(self.python_script_input, 1)
        python_layout.addWidget(self.python_script_browse_button, 0)

        self.script_stack = QStackedWidget()
        self.script_stack.addWidget(QWidget())
        self.script_stack.addWidget(self.action_script_combo)
        self.script_stack.addWidget(python_row)

        self.run_mode_combo = QComboBox()
        self.run_mode_combo.addItem("Target Only", RunMode.TARGET_ONLY.value)
        self.run_mode_combo.addItem("Target Then Script", RunMode.TARGET_THEN_SCRIPT.value)
        self.run_mode_combo.addItem("Script Only", RunMode.SCRIPT_ONLY.value)
        self.run_mode_combo.currentIndexChanged.connect(self._apply_type_state)

        self.enabled_checkbox = QCheckBox("Launcher enabled")
        self.enabled_checkbox.setChecked(True)

        form.addRow("Title", self.title_input)
        form.addRow("Type", self.type_combo)
        form.addRow(self.target_label, target_row)
        form.addRow("Script Type", self.script_type_combo)
        form.addRow("Script", self.script_stack)
        form.addRow("Run Mode", self.run_mode_combo)
        form.addRow("", self.enabled_checkbox)

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Save Card")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self._accept_if_valid)

        button_row.addWidget(cancel_button)
        button_row.addWidget(save_button)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(form)
        root_layout.addLayout(button_row)

    def _populate(
        self,
        *,
        item: LauncherItem | None,
        draft: DialogDraft | None,
        preset_type: LauncherType | None,
        preset_target: str | None,
    ) -> None:
        if item is not None:
            self.title_input.setText(item.title)
            self.type_combo.setCurrentIndex(self.type_combo.findData(item.type.value))
            self.target_input.setText(item.target)
            self.script_type_combo.setCurrentIndex(self.script_type_combo.findData(item.script_type.value))
            self._set_script_value(item.script_name)
            self.run_mode_combo.setCurrentIndex(self.run_mode_combo.findData(item.run_mode.value))
            self.enabled_checkbox.setChecked(item.enabled)
            return

        card_type = preset_type or (draft.type if draft else LauncherType.URL)
        self.type_combo.setCurrentIndex(self.type_combo.findData(card_type.value))
        if draft is not None and draft.type is card_type:
            self.title_input.setText(draft.title)
            self.target_input.setText(preset_target or draft.target)
            self.script_type_combo.setCurrentIndex(self.script_type_combo.findData(draft.script_type.value))
            self._set_script_value(draft.script)
            self.run_mode_combo.setCurrentIndex(self.run_mode_combo.findData(draft.run_mode.value))
            self.enabled_checkbox.setChecked(draft.enabled)
            return

        self.title_input.setText(draft.title if draft else "")
        self.target_input.setText(preset_target or (draft.target if draft else ""))
        self.script_type_combo.setCurrentIndex(
            self.script_type_combo.findData((draft.script_type if draft else ScriptType.NONE).value)
        )
        self._set_script_value(draft.script if draft else "")
        run_mode = draft.run_mode if draft else RunMode.TARGET_ONLY
        self.run_mode_combo.setCurrentIndex(self.run_mode_combo.findData(run_mode.value))
        self.enabled_checkbox.setChecked(draft.enabled if draft else True)

    def _current_type(self) -> LauncherType:
        return LauncherType(self.type_combo.currentData())

    def _current_run_mode(self) -> RunMode:
        return RunMode(self.run_mode_combo.currentData())

    def _current_script_type(self) -> ScriptType:
        return ScriptType(self.script_type_combo.currentData())

    def _current_script_value(self) -> str:
        if self._current_script_type() is ScriptType.PYTHON_FILE:
            return self.python_script_input.text().strip()
        if self._current_script_type() is ScriptType.BUILT_IN_ACTION:
            return self.action_script_combo.currentText().strip()
        return ""

    def _set_script_value(self, value: str) -> None:
        normalized = value.strip()
        self.action_script_combo.setEditText(normalized)
        self.python_script_input.setText(normalized)

    def _suggest_title(self, card_type: LauncherType, target: str) -> str:
        if card_type is LauncherType.URL:
            parsed = urlparse(target)
            host = parsed.netloc.strip().lower()
            if host.startswith("www."):
                host = host[4:]
            return host or target

        exe_path = Path(os.path.expandvars(target)).expanduser()
        return exe_path.stem or exe_path.name or target

    def _apply_type_state(self, *_args) -> None:
        current_type = self._current_type()
        current_run_mode = self._current_run_mode()
        current_script_type = self._current_script_type()

        target_is_optional = current_run_mode is RunMode.SCRIPT_ONLY
        label_prefix = "Optional URL" if target_is_optional and current_type is LauncherType.URL else "URL"
        if current_type is LauncherType.EXE:
            label_prefix = "Optional Executable Path" if target_is_optional else "Executable Path"

        self.target_label.setText(label_prefix)
        self.target_input.setPlaceholderText(
            "Optional. Used by the script if needed." if target_is_optional
            else (
                "https://example.com"
                if current_type is LauncherType.URL
                else "C:/Tools/MyTool.exe, launch.cmd, sketch.ino, or shortcut.lnk"
            )
        )
        self.title_input.setPlaceholderText(
            "Optional. Auto-filled from domain" if current_type is LauncherType.URL else "Optional. Auto-filled from file name"
        )
        self.target_browse_button.setVisible(current_type is LauncherType.EXE)
        self.script_stack.setCurrentIndex({
            ScriptType.NONE: 0,
            ScriptType.BUILT_IN_ACTION: 1,
            ScriptType.PYTHON_FILE: 2,
        }[current_script_type])

        if self.action_script_combo.lineEdit() is not None:
            if current_run_mode is RunMode.TARGET_ONLY:
                action_placeholder = "Optional. Runs only if you choose an action type."
            elif current_run_mode is RunMode.TARGET_THEN_SCRIPT:
                action_placeholder = "Required. Runs after the target."
            else:
                action_placeholder = "Required. Runs without launching the target."
            self.action_script_combo.lineEdit().setPlaceholderText(action_placeholder)

        if current_script_type is ScriptType.PYTHON_FILE and not self.python_script_input.text().strip():
            self.python_script_input.setPlaceholderText(
                r"scripts/examples/context_dump.py or C:/Automation/login_site.py"
            )

        self.script_type_combo.setEnabled(True)

        self._last_type = current_type

    def _browse_target(self) -> None:
        if self._current_type() is not LauncherType.EXE:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Application Target",
            str(Path.home()),
            supported_target_file_dialog_filter(),
        )
        if file_path:
            self.target_input.setText(file_path)
            if not self.title_input.text().strip():
                self.title_input.setText(Path(file_path).stem)

    def _browse_python_script(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python Script",
            str(Path.home()),
            "Python Files (*.py)",
        )
        if file_path:
            self.python_script_input.setText(file_path)

    def _accept_if_valid(self) -> None:
        title = self.title_input.text().strip()
        target = self.target_input.text().strip()
        script_type = self._current_script_type()
        script = self._current_script_value()
        enabled = self.enabled_checkbox.isChecked()
        card_type = self._current_type()
        run_mode = self._current_run_mode()

        if not target and run_mode is not RunMode.SCRIPT_ONLY:
            QMessageBox.warning(self, "Validation Error", "Target is required.")
            return

        if script_type is ScriptType.NONE:
            script = ""

        if run_mode in {RunMode.TARGET_THEN_SCRIPT, RunMode.SCRIPT_ONLY} and not script:
            QMessageBox.warning(
                self,
                "Validation Error",
                "A script is required for 'Target Then Script' and 'Script Only' modes.",
            )
            return

        if script_type is ScriptType.PYTHON_FILE and script:
            script_path = Path(os.path.expandvars(script)).expanduser()
            try:
                script_path = script_path.resolve(strict=False)
            except OSError:
                pass

            if script_path.suffix.lower() != ".py":
                QMessageBox.warning(self, "Validation Error", "Python script must be a .py file.")
                return
            if not script_path.exists():
                QMessageBox.warning(self, "Validation Error", "The selected Python script does not exist.")
                return
            script = str(script_path)

        if card_type is LauncherType.URL and target:
            parsed = urlparse(target)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                QMessageBox.warning(self, "Validation Error", "Enter a valid HTTP or HTTPS URL.")
                return
        elif card_type is LauncherType.EXE and target:
            exe_path = Path(os.path.expandvars(target)).expanduser()
            try:
                exe_path = exe_path.resolve(strict=False)
            except OSError:
                pass

            if exe_path.suffix.lower() not in {
                ".exe",
                ".com",
                ".lnk",
                ".bat",
                ".cmd",
                ".ps1",
                ".msc",
                ".url",
                ".ino",
                ".pde",
            }:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"Application target must be one of: {supported_target_summary()}",
                )
                return
            if not exe_path.exists():
                QMessageBox.warning(self, "Validation Error", "The selected executable does not exist.")
                return
            target = str(exe_path)

        if not title:
            if target:
                title = self._suggest_title(card_type, target).strip()
            elif script_type is ScriptType.PYTHON_FILE and script:
                title = Path(script).stem.strip()
            else:
                title = script.replace("_", " ").strip().title()

        if not title:
            QMessageBox.warning(self, "Validation Error", "Could not determine a title from the target.")
            return

        description = self._editing_item.description if self._editing_item else ""
        icon = self._editing_item.icon if self._editing_item else None

        item_id = self._editing_item.id if self._editing_item else LauncherItem.create(
            title=title,
            description=description,
            type=card_type,
            target=target,
            script=script,
            script_type=script_type,
            run_mode=run_mode,
            icon=icon,
            enabled=enabled,
        ).id

        self._result_item = LauncherItem(
            id=item_id,
            title=title,
            description=description,
            type=card_type,
            target=target,
            script=script,
            script_type=script_type,
            run_mode=run_mode,
            icon=icon,
            enabled=enabled,
        )
        self.accept()

    def result_item(self) -> LauncherItem | None:
        return self._result_item

    def draft_state(self) -> DialogDraft:
        return DialogDraft(
            title=self.title_input.text().strip(),
            target=self.target_input.text().strip(),
            script=self._current_script_value(),
            type=self._current_type(),
            script_type=self._current_script_type(),
            run_mode=self._current_run_mode(),
            enabled=self.enabled_checkbox.isChecked(),
        )
