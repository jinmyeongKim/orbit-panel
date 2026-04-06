from __future__ import annotations

import logging
import os
from pathlib import Path


SUPPORTED_EXECUTABLE_DROP_SUFFIXES = {".exe", ".lnk"}


def is_supported_executable_drop_path(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXECUTABLE_DROP_SUFFIXES


def resolve_executable_drop_target(path: Path, logger: logging.Logger | None = None) -> Path | None:
    """Normalize an EXE or Windows shortcut path for storage.

    `.lnk` shortcuts are preserved as `.lnk` targets instead of being forced
    into a resolved `.exe` path. This is more robust for Unicode shortcut
    names and still launches correctly on Windows via `os.startfile`.
    """

    expanded_path = Path(os.path.expandvars(str(path))).expanduser()
    try:
        normalized = expanded_path.resolve(strict=True)
    except OSError:
        if logger is not None:
            logger.warning("Dropped executable target could not be resolved: %s", path)
        return None

    if not is_supported_executable_drop_path(normalized):
        if logger is not None:
            logger.warning("Dropped target is not an EXE or Windows shortcut: %s", normalized)
        return None

    return normalized
