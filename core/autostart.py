from __future__ import annotations

import logging
from pathlib import Path
import shutil
import sys
import winreg

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "Orbit Panel"


def _launch_command() -> str | None:
    """Build the command Windows should run at login for the current install mode."""
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'

    main_script = Path(__file__).resolve().parent.parent / "main.py"
    if not main_script.exists():
        return None

    # Prefer pythonw so no console window flashes at login.
    interpreter = Path(sys.executable)
    pythonw = interpreter.with_name("pythonw.exe")
    if pythonw.exists():
        interpreter = pythonw
    else:
        hit = shutil.which("pythonw")
        if hit:
            interpreter = Path(hit)

    return f'"{interpreter}" "{main_script}"'


def is_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as key:
            winreg.QueryValueEx(key, RUN_VALUE_NAME)
        return True
    except OSError:
        return False


def set_autostart_enabled(enabled: bool, logger: logging.Logger) -> bool:
    """Register or unregister Orbit Panel in the HKCU Run key. Returns True on success."""
    try:
        if enabled:
            command = _launch_command()
            if command is None:
                logger.error("Cannot enable autostart: launch command could not be resolved.")
                return False
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, command)
            logger.info("Autostart enabled: %s", command)
        else:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                try:
                    winreg.DeleteValue(key, RUN_VALUE_NAME)
                except FileNotFoundError:
                    pass
            logger.info("Autostart disabled")
        return True
    except OSError:
        logger.exception("Failed to update the autostart registry value")
        return False
