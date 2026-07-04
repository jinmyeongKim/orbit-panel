from __future__ import annotations

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Sequence

from core.models import AppConfig, LauncherItem, LauncherType, RunMode, ScriptType, UiState


class ConfigLoader:
    """Load and save launcher cards plus app UI state without mixing UI concerns."""

    def __init__(
        self,
        config_path: Path,
        logger: logging.Logger,
        *,
        legacy_config_path: Path | None = None,
    ) -> None:
        self.config_path = config_path
        self.logger = logger
        self.legacy_config_path = legacy_config_path

    def load_config(self) -> AppConfig:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.config_path.exists():
            if self._migrate_legacy_config():
                return self.load_config()

            defaults = self.default_items()
            config = AppConfig(launcher_items=defaults, ui_state=self.default_ui_state())
            self.save_config(config)
            self.logger.info("Config file missing. Created default config at %s", self.config_path)
            return config

        try:
            raw_text = self.config_path.read_text(encoding="utf-8")
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            self.logger.exception("Invalid JSON detected in %s", self.config_path)
            self._backup_invalid_file()
            defaults = self.default_items()
            config = AppConfig(launcher_items=defaults, ui_state=self.default_ui_state())
            self.save_config(config)
            self.logger.warning("Recovered from invalid JSON with default launcher cards.")
            return config
        except OSError:
            self.logger.exception("Failed to read launcher config from %s", self.config_path)
            defaults = self.default_items()
            self.logger.warning("Using in-memory defaults because config read failed.")
            return AppConfig(launcher_items=defaults, ui_state=self.default_ui_state())

        items: list[LauncherItem]
        ui_state = self.default_ui_state()

        raw_items: Any
        if isinstance(payload, list):
            raw_items = payload
            items = self._parse_items(raw_items)
            self.logger.info("Loaded legacy launcher config format from JSON")
        elif isinstance(payload, dict):
            raw_items = payload.get("launcher_items", [])
            items = self._parse_items(raw_items)
            ui_state = UiState.from_dict(payload.get("ui_state"))
        else:
            self.logger.warning("Launcher config root must be an object or list. Restoring defaults.")
            defaults = self.default_items()
            config = AppConfig(launcher_items=defaults, ui_state=self.default_ui_state())
            self.save_config(config)
            return config

        if not items and raw_items:
            # Every stored item failed to parse. An intentionally empty list stays empty.
            defaults = self.default_items()
            config = AppConfig(launcher_items=defaults, ui_state=self.default_ui_state())
            self.save_config(config)
            self.logger.warning("No valid launcher items found. Restored default cards.")
            return config

        self.logger.info("Loaded %s launcher items from JSON", len(items))
        return AppConfig(launcher_items=items, ui_state=ui_state)

    def load_items(self) -> list[LauncherItem]:
        return self.load_config().launcher_items

    def save_config(self, config: AppConfig) -> None:
        payload = {
            "launcher_items": [item.to_dict() for item in config.launcher_items],
            "ui_state": config.ui_state.to_dict(),
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temp file and swap it in so a crash mid-write never corrupts the config.
        temp_path = self.config_path.with_name(f"{self.config_path.name}.tmp")
        try:
            temp_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            os.replace(temp_path, self.config_path)
        except OSError:
            self.logger.exception("Failed to save launcher items to %s", self.config_path)
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

        self.logger.info(
            "Saved %s launcher items and UI state to JSON",
            len(config.launcher_items),
        )

    def save_items(self, items: Sequence[LauncherItem]) -> None:
        current_ui_state = self.default_ui_state()
        if self.config_path.exists():
            try:
                current_payload = json.loads(self.config_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                current_payload = None
            if isinstance(current_payload, dict):
                current_ui_state = UiState.from_dict(current_payload.get("ui_state"))

        self.save_config(AppConfig(launcher_items=list(items), ui_state=current_ui_state))

    def default_items(self) -> list[LauncherItem]:
        windows_dir = Path(os.environ.get("WINDIR", "C:/Windows"))
        notepad_path = windows_dir / "System32" / "notepad.exe"
        explorer_path = windows_dir / "explorer.exe"
        exe_target = notepad_path if notepad_path.exists() else explorer_path

        return [
            LauncherItem(
                id="sample-task-orbit",
                title="Task Orbit",
                description="Open the daily task orbit dashboard and trigger the URL action hook.",
                type=LauncherType.URL,
                target="https://example.com/task-orbit",
                script="open_task_orbit_action",
                script_type=ScriptType.BUILT_IN_ACTION,
                run_mode=RunMode.TARGET_THEN_SCRIPT,
                icon="",
                enabled=True,
            ),
            LauncherItem(
                id="sample-mail-saver",
                title="Mail Saver",
                description="Launch a Windows executable example and run the mail saver action placeholder.",
                type=LauncherType.EXE,
                target=str(exe_target),
                script="run_mail_saver_action",
                script_type=ScriptType.BUILT_IN_ACTION,
                run_mode=RunMode.TARGET_THEN_SCRIPT,
                icon="",
                enabled=True,
            ),
            LauncherItem(
                id="sample-docs-hub",
                title="Docs Hub",
                description="Quick access to a URL launcher card with the default URL action.",
                type=LauncherType.URL,
                target="https://www.python.org",
                script="",
                script_type=ScriptType.NONE,
                run_mode=RunMode.TARGET_ONLY,
                icon="",
                enabled=True,
            ),
        ]

    def default_ui_state(self) -> UiState:
        return UiState()

    def _parse_items(self, raw_items: Any) -> list[LauncherItem]:
        if not isinstance(raw_items, list):
            self.logger.warning("launcher_items must be a list. Received %s", type(raw_items).__name__)
            return []

        items: list[LauncherItem] = []
        for index, raw_item in enumerate(raw_items):
            try:
                items.append(LauncherItem.from_dict(raw_item))
            except Exception as exc:
                self.logger.warning("Skipping invalid launcher item at index %s: %s", index, exc)

        return items

    def _backup_invalid_file(self) -> None:
        if not self.config_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_path.with_name(
            f"{self.config_path.stem}.broken_{timestamp}{self.config_path.suffix}"
        )

        try:
            self.config_path.replace(backup_path)
        except OSError:
            self.logger.exception("Failed to back up invalid config file: %s", self.config_path)
            return

        self.logger.warning("Backed up invalid config to %s", backup_path)

    def _migrate_legacy_config(self) -> bool:
        if self.legacy_config_path is None:
            return False
        if not self.legacy_config_path.exists():
            return False
        if self.legacy_config_path.resolve() == self.config_path.resolve():
            return False

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.legacy_config_path, self.config_path)
        except OSError:
            self.logger.exception(
                "Failed to migrate legacy config from %s to %s",
                self.legacy_config_path,
                self.config_path,
            )
            return False

        self.logger.info(
            "Migrated legacy config from %s to %s",
            self.legacy_config_path,
            self.config_path,
        )
        return True
