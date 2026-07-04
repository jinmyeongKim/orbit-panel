from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import os
from pathlib import Path
import subprocess
import time
from typing import Callable

from core.models import LauncherItem

ActionHandler = Callable[[LauncherItem, logging.Logger], None]


def _responsive_wait(seconds: float) -> None:
    """Wait without freezing the UI; user input is deferred while waiting."""
    from PySide6.QtCore import QCoreApplication, QEventLoop

    deadline = time.monotonic() + seconds
    app = QCoreApplication.instance()
    while time.monotonic() < deadline:
        if app is not None:
            app.processEvents(QEventLoop.ExcludeUserInputEvents, 50)
        time.sleep(0.02)


def wait_2_seconds(item: LauncherItem, logger: logging.Logger) -> None:
    """Pause for 2 seconds, e.g. to let the launched target finish loading."""
    logger.info("Waiting 2 seconds after '%s'", item.title)
    _responsive_wait(2.0)


def wait_5_seconds(item: LauncherItem, logger: logging.Logger) -> None:
    """Pause for 5 seconds, e.g. to let the launched target finish loading."""
    logger.info("Waiting 5 seconds after '%s'", item.title)
    _responsive_wait(5.0)


def copy_target_to_clipboard(item: LauncherItem, logger: logging.Logger) -> None:
    """Copy the item target (URL or path) to the Windows clipboard."""
    from PySide6.QtGui import QGuiApplication

    clipboard = QGuiApplication.clipboard()
    clipboard.setText(item.target)
    logger.info("Copied target of '%s' to clipboard: %s", item.title, item.target)


def copy_title_to_clipboard(item: LauncherItem, logger: logging.Logger) -> None:
    """Copy the item title to the Windows clipboard."""
    from PySide6.QtGui import QGuiApplication

    clipboard = QGuiApplication.clipboard()
    clipboard.setText(item.title)
    logger.info("Copied title of '%s' to clipboard", item.title)


def open_target_folder(item: LauncherItem, logger: logging.Logger) -> None:
    """Open Windows Explorer with the item target selected."""
    target_path = Path(os.path.expandvars(item.target)).expanduser()
    if not target_path.exists():
        raise FileNotFoundError(f"Target does not exist: {target_path}")

    logger.info("Opening Explorer for '%s': %s", item.title, target_path)
    subprocess.Popen(["explorer.exe", "/select,", str(target_path)])


def focus_window_matching_title(item: LauncherItem, logger: logging.Logger) -> None:
    """Bring the first visible top-level window whose title contains the item title to the front."""
    fragment = item.title.strip().lower()
    if not fragment:
        raise ValueError("Item title is empty; cannot match a window title.")

    user32 = ctypes.windll.user32
    matches: list[int] = []

    enum_proc_type = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
    )

    def _enum_callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if fragment in buffer.value.lower():
            matches.append(hwnd)
            return False
        return True

    user32.EnumWindows(enum_proc_type(_enum_callback), 0)

    if not matches:
        raise LookupError(f"No visible window title contains {fragment!r}.")

    hwnd = matches[0]
    SW_RESTORE = 9
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    logger.info("Focused window matching '%s'", item.title)


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
        "wait_2_seconds": wait_2_seconds,
        "wait_5_seconds": wait_5_seconds,
        "copy_target_to_clipboard": copy_target_to_clipboard,
        "copy_title_to_clipboard": copy_title_to_clipboard,
        "open_target_folder": open_target_folder,
        "focus_window_matching_title": focus_window_matching_title,
        "browser_login_placeholder_action": browser_login_placeholder_action,
    }
