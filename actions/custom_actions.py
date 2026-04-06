from __future__ import annotations

import logging
from typing import Callable

from core.models import LauncherItem

ActionHandler = Callable[[LauncherItem, logging.Logger], None]


def open_task_orbit_action(item: LauncherItem, logger: logging.Logger) -> None:
    logger.info("open_task_orbit_action invoked for '%s'", item.title)
    # Placeholder for future task automation.
    # Example extensions: pywinauto UI steps, Playwright web steps, or
    # additional subprocess orchestration after the launcher target opens.


def run_mail_saver_action(item: LauncherItem, logger: logging.Logger) -> None:
    logger.info("run_mail_saver_action invoked for '%s'", item.title)
    # Placeholder for future workflow automation.
    # Example extensions: mailbox export routines, file organization, or
    # macro chains that run after the desktop executable is launched.


def default_url_action(item: LauncherItem, logger: logging.Logger) -> None:
    logger.info("default_url_action invoked for '%s'", item.title)
    # Placeholder for future URL post-launch logic.


def default_exe_action(item: LauncherItem, logger: logging.Logger) -> None:
    logger.info("default_exe_action invoked for '%s'", item.title)
    # Placeholder for future executable post-launch logic.


def browser_login_placeholder_action(item: LauncherItem, logger: logging.Logger) -> None:
    logger.info("browser_login_placeholder_action invoked for '%s' (target=%s)", item.title, item.target)
    # Placeholder for future login automation.
    # Recommended approach for web login flows:
    # 1. Read credentials from environment variables or Windows Credential Manager.
    # 2. Use Playwright to launch or attach to a browser session.
    # 3. Navigate to `item.target` if needed.
    # 4. Fill the login form and submit.
    # 5. Add site-specific waits and verification before returning.


def build_default_action_registry() -> dict[str, ActionHandler]:
    return {
        "open_task_orbit_action": open_task_orbit_action,
        "run_mail_saver_action": run_mail_saver_action,
        "default_url_action": default_url_action,
        "default_exe_action": default_exe_action,
        "browser_login_placeholder_action": browser_login_placeholder_action,
    }
