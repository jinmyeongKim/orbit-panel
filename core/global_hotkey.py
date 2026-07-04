from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

HOTKEY_ID = 0xA11
HOTKEY_LABEL = "Ctrl+Alt+O"
_VK_O = 0x4F


class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    """Register Ctrl+Alt+O system-wide and invoke a callback when it fires.

    RegisterHotKey is bound to this (GUI) thread's message queue, so the Qt
    event loop delivers WM_HOTKEY to this native event filter.
    """

    def __init__(self, callback: Callable[[], None], logger: logging.Logger) -> None:
        super().__init__()
        self._callback = callback
        self._logger = logger
        self._registered = False

    @property
    def is_registered(self) -> bool:
        return self._registered

    def register(self) -> bool:
        if self._registered:
            return True

        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, _VK_O):
            self._logger.warning(
                "Global hotkey %s could not be registered (already in use by another app?)",
                HOTKEY_LABEL,
            )
            return False

        self._registered = True
        self._logger.info("Global hotkey %s registered", HOTKEY_LABEL)
        return True

    def unregister(self) -> None:
        if not self._registered:
            return

        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
        self._registered = False
        self._logger.info("Global hotkey %s unregistered", HOTKEY_LABEL)

    def nativeEventFilter(self, event_type, message):
        if self._registered and event_type == b"windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                try:
                    self._callback()
                except Exception:
                    self._logger.exception("Global hotkey callback failed")
                return True, 0
        return False, 0
