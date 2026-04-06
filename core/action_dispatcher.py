from __future__ import annotations

import logging

from actions.custom_actions import ActionHandler, build_default_action_registry
from core.models import LauncherItem


class ActionDispatcher:
    """Dispatch script names to Python action handlers."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self._actions: dict[str, ActionHandler] = build_default_action_registry()

    def available_actions(self) -> list[str]:
        return sorted(self._actions)

    def register_action(self, name: str, handler: ActionHandler) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Action name cannot be empty.")

        self._actions[normalized] = handler
        self.logger.info("Registered action handler '%s'", normalized)

    def dispatch(self, script_name: str, item: LauncherItem) -> bool:
        normalized = script_name.strip()
        if not normalized:
            self.logger.info("No action configured for '%s'", item.title)
            return True

        handler = self._actions.get(normalized)
        if handler is None:
            self.logger.warning("Unknown action '%s' for '%s'", normalized, item.title)
            return False

        self.logger.info("Dispatching action '%s' for '%s'", normalized, item.title)
        try:
            handler(item, self.logger)
        except Exception:
            self.logger.exception("Action '%s' failed for '%s'", normalized, item.title)
            return False

        self.logger.info("Action '%s' completed for '%s'", normalized, item.title)
        return True
