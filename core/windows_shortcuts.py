from __future__ import annotations

import logging
import os
from pathlib import Path


SUPPORTED_EXECUTABLE_DROP_SUFFIXES = {
    ".exe",
    ".com",
    ".lnk",
    ".bat",
    ".cmd",
    ".ps1",
    ".msc",
    ".url",
    ".ino",
    ".pde",
}


def supported_target_file_dialog_filter() -> str:
    return (
        "Application Targets (*.exe *.com *.lnk *.bat *.cmd *.ps1 *.msc *.url *.ino *.pde)"
    )


def supported_target_summary() -> str:
    return ".exe, .com, .lnk, .bat, .cmd, .ps1, .msc, .url, .ino, .pde"


def is_supported_executable_drop_path(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXECUTABLE_DROP_SUFFIXES


def resolve_executable_drop_target(path: Path, logger: logging.Logger | None = None) -> Path | None:
    """Normalize a supported Windows launch target for storage.

    `.lnk` shortcuts and other Windows shell-handled target types are preserved
    as their original paths instead of being resolved into another executable.
    """

    expanded_path = Path(os.path.expandvars(str(path))).expanduser()
    try:
        normalized = expanded_path.resolve(strict=True)
    except OSError:
        if logger is not None:
            logger.warning("Dropped application target could not be resolved: %s", path)
        return None

    if not is_supported_executable_drop_path(normalized):
        if logger is not None:
            logger.warning("Dropped target is not a supported Windows launch target: %s", normalized)
        return None

    return normalized
