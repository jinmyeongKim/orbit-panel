from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from core.launcher import ItemExecutionReport, LauncherService
from core.models import LauncherItem, Scenario


class ScenarioRunner(QObject):
    """Run scenario steps sequentially on the UI event loop, honoring per-step delays."""

    step_started = Signal(str, int, int)  # scenario name, step number, total steps
    step_finished = Signal(object)  # ItemExecutionReport
    scenario_finished = Signal(str, int, int)  # scenario name, ok count, total steps

    def __init__(
        self,
        launcher_service: LauncherService,
        logger: logging.Logger,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.launcher_service = launcher_service
        self.logger = logger
        self._running = False
        self._scenario_name = ""
        self._pending: list[tuple[float, LauncherItem]] = []
        self._total_steps = 0
        self._ok_count = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def run(self, scenario: Scenario, item_lookup: dict[str, LauncherItem]) -> bool:
        """Start a scenario. Returns False when a run is already in progress or nothing is runnable."""
        if self._running:
            self.logger.warning(
                "Scenario '%s' requested while '%s' is still running", scenario.name, self._scenario_name
            )
            return False

        pending: list[tuple[float, LauncherItem]] = []
        for step in scenario.steps:
            item = item_lookup.get(step.item_id)
            if item is None:
                self.logger.warning(
                    "Scenario '%s' skips a step: item %s no longer exists", scenario.name, step.item_id
                )
                continue
            if not item.enabled:
                self.logger.info(
                    "Scenario '%s' skips disabled item '%s'", scenario.name, item.title
                )
                continue
            pending.append((max(0.0, step.delay_seconds), item))

        if not pending:
            self.logger.warning("Scenario '%s' has no runnable steps", scenario.name)
            return False

        self._running = True
        self._scenario_name = scenario.name
        self._pending = pending
        self._total_steps = len(pending)
        self._ok_count = 0
        self.logger.info("Scenario '%s' started with %s step(s)", scenario.name, self._total_steps)
        self._schedule_next()
        return True

    def _schedule_next(self) -> None:
        if not self._pending:
            self._finish()
            return

        delay_seconds, _item = self._pending[0]
        QTimer.singleShot(int(delay_seconds * 1000), self._execute_next)

    def _execute_next(self) -> None:
        if not self._pending:
            self._finish()
            return

        _delay, item = self._pending.pop(0)
        step_number = self._total_steps - len(self._pending)
        self.step_started.emit(self._scenario_name, step_number, self._total_steps)

        report: ItemExecutionReport = self.launcher_service.execute_item(item)
        if report.success:
            self._ok_count += 1
        self.step_finished.emit(report)

        self._schedule_next()

    def _finish(self) -> None:
        name = self._scenario_name
        ok_count = self._ok_count
        total = self._total_steps

        self._running = False
        self._scenario_name = ""
        self._pending = []
        self._total_steps = 0
        self._ok_count = 0

        self.logger.info("Scenario '%s' finished: %s/%s step(s) ok", name, ok_count, total)
        self.scenario_finished.emit(name, ok_count, total)
