from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QVBoxLayout

from core.logger import LogStore


class LogPanel(QFrame):
    def __init__(self, log_store: LogStore, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("LogPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Activity Log")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Startup, JSON saves, app and URL launches, action hooks, drag-and-drop, and errors.")
        subtitle.setObjectName("SectionSubtitle")
        subtitle.setWordWrap(True)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("LogEditor")
        self.editor.setReadOnly(True)
        self.editor.setMinimumHeight(190)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.editor, 1)

        for line in log_store.snapshot():
            self.editor.appendPlainText(line)

        log_store.log_received.connect(self.append_log)

    @Slot(str)
    def append_log(self, line: str) -> None:
        self.editor.appendPlainText(line)
        self.editor.verticalScrollBar().setValue(self.editor.verticalScrollBar().maximum())
