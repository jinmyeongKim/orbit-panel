from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models import LauncherItem, Scenario, ScenarioStep


class ScenarioStepRow(QFrame):
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    remove_requested = Signal(object)

    def __init__(
        self,
        items: Sequence[LauncherItem],
        *,
        selected_item_id: str | None = None,
        delay_seconds: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ScenarioStepRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.order_label = QLabel("1")
        self.order_label.setObjectName("OrderBadge")
        self.order_label.setAlignment(Qt.AlignCenter)

        self.item_combo = QComboBox()
        for item in items:
            self.item_combo.addItem(f"{item.title}  ({item.type_label})", item.id)
        if selected_item_id is not None:
            index = self.item_combo.findData(selected_item_id)
            if index >= 0:
                self.item_combo.setCurrentIndex(index)

        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 600.0)
        self.delay_spin.setDecimals(1)
        self.delay_spin.setSingleStep(0.5)
        self.delay_spin.setSuffix(" s wait")
        self.delay_spin.setValue(max(0.0, delay_seconds))
        self.delay_spin.setToolTip("Wait this long before running this step.")

        up_button = QPushButton("▲")
        up_button.setObjectName("ItemSecondaryAction")
        up_button.setFixedWidth(40)
        up_button.clicked.connect(lambda: self.move_up_requested.emit(self))

        down_button = QPushButton("▼")
        down_button.setObjectName("ItemSecondaryAction")
        down_button.setFixedWidth(40)
        down_button.clicked.connect(lambda: self.move_down_requested.emit(self))

        remove_button = QPushButton("✕")
        remove_button.setObjectName("ItemDangerAction")
        remove_button.setFixedWidth(40)
        remove_button.clicked.connect(lambda: self.remove_requested.emit(self))

        layout.addWidget(self.order_label, 0)
        layout.addWidget(self.item_combo, 1)
        layout.addWidget(self.delay_spin, 0)
        layout.addWidget(up_button, 0)
        layout.addWidget(down_button, 0)
        layout.addWidget(remove_button, 0)

    def set_order(self, order: int) -> None:
        self.order_label.setText(str(order))

    def to_step(self) -> ScenarioStep | None:
        item_id = self.item_combo.currentData()
        if not item_id:
            return None
        return ScenarioStep(item_id=str(item_id), delay_seconds=float(self.delay_spin.value()))


class ScenarioDialog(QDialog):
    """Create or edit a scenario: a named, ordered list of items with per-step delays."""

    def __init__(
        self,
        *,
        items: Sequence[LauncherItem],
        scenario: Scenario | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._items = list(items)
        self._editing_scenario = scenario
        self._result_scenario: Scenario | None = None
        self._step_rows: list[ScenarioStepRow] = []

        self.setWindowTitle("Edit Scenario" if scenario else "New Scenario")
        self.setModal(True)
        self.setMinimumSize(640, 480)

        self._build_ui()
        self._populate(scenario)

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 22, 22, 22)
        root_layout.setSpacing(14)

        title = QLabel("Scenario")
        title.setObjectName("SectionTitle")
        subtitle = QLabel(
            "Steps run top to bottom. Each step can wait before it starts — "
            "useful to let an app or page finish loading."
        )
        subtitle.setObjectName("SectionSubtitle")
        subtitle.setWordWrap(True)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Scenario name, e.g. Morning Routine")

        steps_scroll = QScrollArea()
        steps_scroll.setWidgetResizable(True)
        steps_scroll.setFrameShape(QFrame.NoFrame)

        steps_host = QWidget()
        self.steps_layout = QVBoxLayout(steps_host)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_layout.setSpacing(10)
        self.steps_layout.addStretch(1)
        steps_scroll.setWidget(steps_host)

        add_step_button = QPushButton("+ Add Step")
        add_step_button.setObjectName("GhostActionButton")
        add_step_button.clicked.connect(self._add_step_row)

        button_row = QHBoxLayout()
        button_row.addWidget(add_step_button, 0, Qt.AlignLeft)
        button_row.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Save Scenario")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self._accept_if_valid)

        button_row.addWidget(cancel_button)
        button_row.addWidget(save_button)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(self.name_input)
        root_layout.addWidget(steps_scroll, 1)
        root_layout.addLayout(button_row)

    def _populate(self, scenario: Scenario | None) -> None:
        if scenario is None:
            self._add_step_row()
            return

        self.name_input.setText(scenario.name)
        known_ids = {item.id for item in self._items}
        for step in scenario.steps:
            if step.item_id in known_ids:
                self._add_step_row(selected_item_id=step.item_id, delay_seconds=step.delay_seconds)
        if not self._step_rows:
            self._add_step_row()

    def _add_step_row(
        self,
        *,
        selected_item_id: str | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        if not self._items:
            QMessageBox.information(
                self,
                "No Items",
                "Add URL or EXE items to Orbit Panel first, then compose them into a scenario.",
            )
            return

        row = ScenarioStepRow(
            self._items,
            selected_item_id=selected_item_id,
            delay_seconds=delay_seconds,
        )
        row.move_up_requested.connect(self._move_row_up)
        row.move_down_requested.connect(self._move_row_down)
        row.remove_requested.connect(self._remove_row)

        self._step_rows.append(row)
        self.steps_layout.insertWidget(self.steps_layout.count() - 1, row)
        self._refresh_order_labels()

    def _move_row_up(self, row: ScenarioStepRow) -> None:
        index = self._step_rows.index(row)
        if index <= 0:
            return
        self._step_rows[index - 1], self._step_rows[index] = (
            self._step_rows[index],
            self._step_rows[index - 1],
        )
        self._relayout_rows()

    def _move_row_down(self, row: ScenarioStepRow) -> None:
        index = self._step_rows.index(row)
        if index >= len(self._step_rows) - 1:
            return
        self._step_rows[index], self._step_rows[index + 1] = (
            self._step_rows[index + 1],
            self._step_rows[index],
        )
        self._relayout_rows()

    def _remove_row(self, row: ScenarioStepRow) -> None:
        self._step_rows.remove(row)
        self.steps_layout.removeWidget(row)
        row.deleteLater()
        self._refresh_order_labels()

    def _relayout_rows(self) -> None:
        for row in self._step_rows:
            self.steps_layout.removeWidget(row)
        for index, row in enumerate(self._step_rows):
            self.steps_layout.insertWidget(index, row)
        self._refresh_order_labels()

    def _refresh_order_labels(self) -> None:
        for index, row in enumerate(self._step_rows, start=1):
            row.set_order(index)

    def _accept_if_valid(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Scenario name is required.")
            return

        steps = [step for step in (row.to_step() for row in self._step_rows) if step is not None]
        if not steps:
            QMessageBox.warning(self, "Validation Error", "Add at least one step.")
            return

        if self._editing_scenario is not None:
            self._result_scenario = Scenario(
                id=self._editing_scenario.id,
                name=name,
                steps=steps,
            )
        else:
            self._result_scenario = Scenario.create(name=name, steps=steps)
        self.accept()

    def result_scenario(self) -> Scenario | None:
        return self._result_scenario
