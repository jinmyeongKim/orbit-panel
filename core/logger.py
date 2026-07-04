from __future__ import annotations

from collections import deque
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QObject, Signal


class LogStore(QObject):
    """Store log lines for the UI and emit them as they arrive."""

    log_received = Signal(str)

    def __init__(self, max_entries: int = 1500) -> None:
        super().__init__()
        self._entries: deque[str] = deque(maxlen=max_entries)

    def append(self, message: str) -> None:
        self._entries.append(message)
        self.log_received.emit(message)

    def snapshot(self) -> list[str]:
        return list(self._entries)


class QtLogHandler(logging.Handler):
    """Bridge Python logging records into the Qt UI."""

    def __init__(self, store: LogStore) -> None:
        super().__init__()
        self._store = store

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            self.handleError(record)
            return

        self._store.append(message)


def configure_logging(store: LogStore, log_file: Path) -> logging.Logger:
    logger = logging.getLogger("orbit_panel")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    ui_handler = QtLogHandler(store)
    ui_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(ui_handler)
    return logger
