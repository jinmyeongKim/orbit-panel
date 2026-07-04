from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models import Scenario


class ScenarioChip(QFrame):
    run_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, scenario: Scenario, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ScenarioChip")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 12, 10)
        layout.setSpacing(10)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)

        name_label = QLabel(scenario.name)
        name_label.setObjectName("ScenarioName")

        step_count = len(scenario.steps)
        meta_label = QLabel(f"{step_count} step{'s' if step_count != 1 else ''}")
        meta_label.setObjectName("ScenarioMeta")

        text_column.addWidget(name_label)
        text_column.addWidget(meta_label)

        run_button = QPushButton("Run")
        run_button.setObjectName("CompactPrimaryButton")
        run_button.clicked.connect(lambda: self.run_requested.emit(scenario.id))

        edit_button = QPushButton("Edit")
        edit_button.setObjectName("FlatActionButton")
        edit_button.clicked.connect(lambda: self.edit_requested.emit(scenario.id))

        delete_button = QPushButton("✕")
        delete_button.setObjectName("CompactDangerButton")
        delete_button.setFixedWidth(36)
        delete_button.setToolTip("Delete scenario")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(scenario.id))

        layout.addLayout(text_column, 1)
        layout.addWidget(run_button, 0)
        layout.addWidget(edit_button, 0)
        layout.addWidget(delete_button, 0)


class ScenarioStrip(QFrame):
    """Horizontal strip listing saved scenarios with one-click run."""

    run_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    create_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GroupPanel")

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(20, 14, 20, 14)
        root_layout.setSpacing(14)

        title_column = QVBoxLayout()
        title_column.setSpacing(2)

        title_label = QLabel("Scenarios")
        title_label.setObjectName("SectionTitle")

        subtitle_label = QLabel("One click runs a sequence of items with delays.")
        subtitle_label.setObjectName("SectionSubtitle")

        title_column.addWidget(title_label)
        title_column.addWidget(subtitle_label)

        self.chips_scroll = QScrollArea()
        self.chips_scroll.setWidgetResizable(True)
        self.chips_scroll.setFrameShape(QFrame.NoFrame)
        self.chips_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chips_scroll.setFixedHeight(72)

        self.chips_host = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_host)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(10)
        self.chips_layout.addStretch(1)
        self.chips_scroll.setWidget(self.chips_host)

        new_button = QPushButton("+ New Scenario")
        new_button.setObjectName("GhostActionButton")
        new_button.clicked.connect(self.create_requested)

        root_layout.addLayout(title_column, 0)
        root_layout.addWidget(self.chips_scroll, 1)
        root_layout.addWidget(new_button, 0)

    def set_scenarios(self, scenarios: Sequence[Scenario]) -> None:
        while self.chips_layout.count() > 1:
            layout_item = self.chips_layout.takeAt(0)
            widget = layout_item.widget()
            if widget is not None:
                widget.deleteLater()

        if not scenarios:
            empty_label = QLabel("No scenarios yet. Compose your items into a one-click routine.")
            empty_label.setObjectName("ScenarioMeta")
            self.chips_layout.insertWidget(0, empty_label)
            return

        for index, scenario in enumerate(scenarios):
            chip = ScenarioChip(scenario)
            chip.run_requested.connect(self.run_requested)
            chip.edit_requested.connect(self.edit_requested)
            chip.delete_requested.connect(self.delete_requested)
            self.chips_layout.insertWidget(index, chip)
