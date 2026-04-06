from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Resolve runtime paths in a way that also works for PyInstaller builds.

    In source mode, JSON and log files live in the project-level `config/`
    and `logs/` folders. In frozen Windows builds, runtime state is stored
    under `%AppData%\\Orbit Panel` while static assets remain beside the EXE.
    """

    base_dir: Path
    runtime_dir: Path
    config_dir: Path
    assets_dir: Path
    icons_dir: Path
    logs_dir: Path
    legacy_config_dir: Path | None = None

    @classmethod
    def discover(cls) -> "AppPaths":
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
            resource_base_dir = Path(getattr(sys, "_MEIPASS", base_dir)).resolve()
            appdata_root = Path(
                os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
            )
            runtime_dir = appdata_root / "Orbit Panel"
            config_dir = runtime_dir / "config"
            logs_dir = runtime_dir / "logs"
            legacy_config_dir = base_dir / "config"
        else:
            base_dir = Path(__file__).resolve().parent.parent
            resource_base_dir = base_dir
            runtime_dir = base_dir
            config_dir = base_dir / "config"
            logs_dir = base_dir / "logs"
            legacy_config_dir = None

        return cls(
            base_dir=base_dir,
            runtime_dir=runtime_dir,
            config_dir=config_dir,
            assets_dir=resource_base_dir / "assets",
            icons_dir=resource_base_dir / "assets" / "icons",
            logs_dir=logs_dir,
            legacy_config_dir=legacy_config_dir,
        )

    @property
    def config_file(self) -> Path:
        return self.config_dir / "launcher_items.json"

    @property
    def legacy_config_file(self) -> Path | None:
        if self.legacy_config_dir is None:
            return None
        return self.legacy_config_dir / "launcher_items.json"

    @property
    def app_icon_file(self) -> Path:
        return self.icons_dir / "orbit_panel.ico"

    @property
    def app_icon_preview_file(self) -> Path:
        return self.icons_dir / "orbit_panel.png"

    @property
    def log_file(self) -> Path:
        return self.logs_dir / "orbit_panel.log"

    def ensure_runtime_dirs(self) -> None:
        for directory in (self.runtime_dir, self.config_dir, self.assets_dir, self.icons_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)
