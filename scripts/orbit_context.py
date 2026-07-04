from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any


@dataclass(slots=True)
class OrbitItemContext:
    item_id: str
    title: str
    item_type: str
    target: str
    run_mode: str
    script_type: str
    script_value: str
    enabled: bool
    runtime_dir: Path | None
    log_dir: Path | None
    config_file: Path | None
    base_dir: Path | None
    helpers_dir: Path | None
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = dict(self.raw)
        data.update(
            {
                "id": self.item_id,
                "title": self.title,
                "type": self.item_type,
                "target": self.target,
                "run_mode": self.run_mode,
                "script_type": self.script_type,
                "script": self.script_value,
                "enabled": self.enabled,
                "runtime_dir": str(self.runtime_dir) if self.runtime_dir else "",
                "log_dir": str(self.log_dir) if self.log_dir else "",
                "config_file": str(self.config_file) if self.config_file else "",
                "base_dir": str(self.base_dir) if self.base_dir else "",
                "helpers_dir": str(self.helpers_dir) if self.helpers_dir else "",
            }
        )
        return data


def _path_from_env(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    return Path(value)


def load_context() -> OrbitItemContext:
    raw_json = os.environ.get("ORBIT_PANEL_ITEM_CONTEXT", "").strip()
    payload: dict[str, Any] = {}
    if raw_json:
        try:
            decoded = json.loads(raw_json)
            if isinstance(decoded, dict):
                payload = decoded
        except json.JSONDecodeError:
            payload = {}

    item_id = str(payload.get("id") or os.environ.get("ORBIT_PANEL_ITEM_ID") or "").strip()
    title = str(payload.get("title") or os.environ.get("ORBIT_PANEL_ITEM_TITLE") or "").strip()
    item_type = str(payload.get("type") or os.environ.get("ORBIT_PANEL_ITEM_TYPE") or "").strip()
    target = str(payload.get("target") or os.environ.get("ORBIT_PANEL_ITEM_TARGET") or "").strip()
    run_mode = str(payload.get("run_mode") or os.environ.get("ORBIT_PANEL_RUN_MODE") or "").strip()
    script_type = str(payload.get("script_type") or os.environ.get("ORBIT_PANEL_SCRIPT_TYPE") or "").strip()
    script_value = str(payload.get("script") or os.environ.get("ORBIT_PANEL_SCRIPT_VALUE") or "").strip()
    enabled = bool(payload.get("enabled", os.environ.get("ORBIT_PANEL_ITEM_ENABLED", "true").lower() == "true"))

    return OrbitItemContext(
        item_id=item_id,
        title=title,
        item_type=item_type,
        target=target,
        run_mode=run_mode,
        script_type=script_type,
        script_value=script_value,
        enabled=enabled,
        runtime_dir=_path_from_env("ORBIT_PANEL_RUNTIME_DIR"),
        log_dir=_path_from_env("ORBIT_PANEL_LOG_DIR"),
        config_file=_path_from_env("ORBIT_PANEL_CONFIG_FILE"),
        base_dir=_path_from_env("ORBIT_PANEL_BASE_DIR"),
        helpers_dir=_path_from_env("ORBIT_PANEL_HELPERS_DIR"),
        raw=payload,
    )


def default_log_file(script_name: str | None = None) -> Path:
    context = load_context()
    if context.log_dir is not None:
        context.log_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(script_name).stem if script_name else Path(sys.argv[0]).stem
        return context.log_dir / f"{stem}.log"

    return Path.cwd() / f"{Path(sys.argv[0]).stem}.log"


def build_logger(script_name: str | None = None) -> logging.Logger:
    logger_name = f"orbit_script.{Path(script_name or sys.argv[0]).stem}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(default_log_file(script_name), encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

