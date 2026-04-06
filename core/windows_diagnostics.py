from __future__ import annotations

import ctypes
import logging
import os
import sys


def is_process_elevated() -> bool | None:
    """Return whether the current process is elevated on Windows.

    Returns `None` when elevation cannot be determined.
    """

    if os.name != "nt":
        return None

    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return None


def log_drag_and_drop_diagnostics(logger: logging.Logger) -> None:
    """Log likely causes when Explorer file drops are blocked."""

    elevated = is_process_elevated()
    if elevated is True:
        logger.warning(
            "Orbit Panel is running elevated. Windows Explorer drag-and-drop may show a blocked cursor "
            "unless Explorer is also elevated."
        )
        return

    if elevated is False:
        logger.info("Orbit Panel is running at normal user level. Explorer drag-and-drop should be allowed.")
        return

    logger.warning("Could not determine process elevation state for drag-and-drop diagnostics.")


def set_app_user_model_id(app_id: str, logger: logging.Logger | None = None) -> bool:
    """Set a stable Windows AppUserModelID for taskbar and title-bar icon binding."""

    if sys.platform != "win32":
        return False

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        if logger is not None:
            logger.exception("Failed to set AppUserModelID: %s", app_id)
        return False

    if logger is not None:
        logger.info("Set AppUserModelID: %s", app_id)
    return True
