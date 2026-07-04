from __future__ import annotations

from pathlib import Path

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
    QVBoxLayout,
    QWidget,
)

from core.autostart import is_autostart_enabled
from core.global_hotkey import HOTKEY_LABEL
from core.models import AppSettings, BrowserChoice


class SettingsDialog(QDialog):
    def __init__(self, *, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self._result_settings: AppSettings | None = None

        self.setWindowTitle("Orbit Panel Settings")
        self.setModal(True)
        self.setMinimumWidth(520)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 22, 22, 22)
        root_layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Choose how URLs open and how Orbit Panel stays available.")
        subtitle.setObjectName("SectionSubtitle")
        subtitle.setWordWrap(True)

        form = QFormLayout()
        form.setSpacing(14)

        self.browser_combo = QComboBox()
        self.browser_combo.addItem("System default browser", BrowserChoice.SYSTEM_DEFAULT.value)
        self.browser_combo.addItem("Google Chrome", BrowserChoice.CHROME.value)
        self.browser_combo.addItem("Microsoft Edge", BrowserChoice.EDGE.value)
        self.browser_combo.addItem("Custom browser...", BrowserChoice.CUSTOM.value)
        self.browser_combo.setCurrentIndex(self.browser_combo.findData(settings.browser.value))
        self.browser_combo.currentIndexChanged.connect(self._apply_browser_state)

        self.custom_browser_input = QLineEdit(settings.custom_browser_path)
        self.custom_browser_input.setPlaceholderText(r"C:\Program Files\Mozilla Firefox\firefox.exe")

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse_browser)

        self.custom_browser_row = QWidget()
        custom_layout = QHBoxLayout(self.custom_browser_row)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(10)
        custom_layout.addWidget(self.custom_browser_input, 1)
        custom_layout.addWidget(browse_button, 0)

        self.autostart_checkbox = QCheckBox("Start Orbit Panel when Windows starts")
        self.autostart_checkbox.setChecked(is_autostart_enabled())

        self.tray_checkbox = QCheckBox("Keep running in the system tray when the window is closed")
        self.tray_checkbox.setChecked(settings.minimize_to_tray)

        self.hotkey_checkbox = QCheckBox(f"Global hotkey {HOTKEY_LABEL} shows / hides the window")
        self.hotkey_checkbox.setChecked(settings.global_hotkey_enabled)

        form.addRow("Open URLs with", self.browser_combo)
        form.addRow("Browser path", self.custom_browser_row)
        form.addRow("", self.autostart_checkbox)
        form.addRow("", self.tray_checkbox)
        form.addRow("", self.hotkey_checkbox)

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Save Settings")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self._accept_if_valid)

        button_row.addWidget(cancel_button)
        button_row.addWidget(save_button)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(form)
        root_layout.addLayout(button_row)

        self._apply_browser_state()

    def _apply_browser_state(self, *_args) -> None:
        is_custom = self.browser_combo.currentData() == BrowserChoice.CUSTOM.value
        self.custom_browser_row.setEnabled(is_custom)

    def _browse_browser(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Browser Executable",
            str(Path.home()),
            "Executable Files (*.exe)",
        )
        if file_path:
            self.custom_browser_input.setText(file_path)

    def _accept_if_valid(self) -> None:
        browser = BrowserChoice(self.browser_combo.currentData())
        custom_path = self.custom_browser_input.text().strip()

        if browser is BrowserChoice.CUSTOM:
            if not custom_path:
                QMessageBox.warning(self, "Validation Error", "Choose a browser executable.")
                return
            if not Path(custom_path).exists():
                QMessageBox.warning(self, "Validation Error", "The browser executable does not exist.")
                return

        self._result_settings = AppSettings(
            browser=browser,
            custom_browser_path=custom_path,
            minimize_to_tray=self.tray_checkbox.isChecked(),
            global_hotkey_enabled=self.hotkey_checkbox.isChecked(),
        )
        self.accept()

    def result_settings(self) -> AppSettings | None:
        return self._result_settings

    def autostart_requested(self) -> bool:
        return self.autostart_checkbox.isChecked()
