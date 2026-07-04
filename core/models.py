from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, TypeVar
from urllib.parse import urlparse
import uuid

_EnumT = TypeVar("_EnumT", bound=Enum)


def _enum_or_none(enum_cls: type[_EnumT], value: Any) -> _EnumT | None:
    try:
        return enum_cls(value)
    except ValueError:
        return None


def suggest_url_title(target: str) -> str:
    """Derive a display title from a URL, e.g. 'https://www.foo.com/x' -> 'foo.com'."""
    host = urlparse(target).netloc.strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return host or target


class LauncherType(str, Enum):
    URL = "url"
    EXE = "exe"


class RunMode(str, Enum):
    TARGET_ONLY = "target_only"
    TARGET_THEN_SCRIPT = "target_then_script"
    SCRIPT_ONLY = "script_only"


class ScriptType(str, Enum):
    NONE = "none"
    BUILT_IN_ACTION = "built_in_action"
    PYTHON_FILE = "python_file"


@dataclass(slots=True)
class DialogDraft:
    title: str = ""
    target: str = ""
    script: str = ""
    type: LauncherType = LauncherType.URL
    script_type: ScriptType = ScriptType.NONE
    run_mode: RunMode = RunMode.TARGET_ONLY
    enabled: bool = True

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> "DialogDraft":
        if not raw or not isinstance(raw, Mapping):
            return cls()

        raw_type = str(raw.get("type") or LauncherType.URL.value).strip().lower()
        launcher_type = _enum_or_none(LauncherType, raw_type) or LauncherType.URL
        raw_run_mode = str(raw.get("run_mode") or RunMode.TARGET_ONLY.value).strip().lower()
        run_mode = _enum_or_none(RunMode, raw_run_mode) or RunMode.TARGET_ONLY
        raw_script = str(raw.get("script") or "").strip()
        raw_script_type = str(raw.get("script_type") or "").strip().lower()
        script_type = _enum_or_none(ScriptType, raw_script_type)
        if script_type is None:
            script_type = ScriptType.BUILT_IN_ACTION if raw_script else ScriptType.NONE

        return cls(
            title=str(raw.get("title") or "").strip(),
            target=str(raw.get("target") or "").strip(),
            script=raw_script,
            type=launcher_type,
            script_type=script_type,
            run_mode=run_mode,
            enabled=bool(raw.get("enabled", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "target": self.target,
            "script": self.script,
            "script_type": self.script_type.value,
            "type": self.type.value,
            "run_mode": self.run_mode.value,
            "enabled": self.enabled,
        }


@dataclass(slots=True)
class UiState:
    window_x: int | None = None
    window_y: int | None = None
    window_width: int = 1460
    window_height: int = 940
    window_maximized: bool = False
    last_url_input: str = ""
    dialog_draft: DialogDraft = field(default_factory=DialogDraft)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> "UiState":
        if not raw or not isinstance(raw, Mapping):
            return cls()

        def _coerce_int(value: Any, fallback: int | None) -> int | None:
            if value is None:
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback

        return cls(
            window_x=_coerce_int(raw.get("window_x"), None),
            window_y=_coerce_int(raw.get("window_y"), None),
            window_width=_coerce_int(raw.get("window_width"), 1460) or 1460,
            window_height=_coerce_int(raw.get("window_height"), 940) or 940,
            window_maximized=bool(raw.get("window_maximized", False)),
            last_url_input=str(raw.get("last_url_input") or "").strip(),
            dialog_draft=DialogDraft.from_dict(raw.get("dialog_draft")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_maximized": self.window_maximized,
            "last_url_input": self.last_url_input,
            "dialog_draft": self.dialog_draft.to_dict(),
        }


class BrowserChoice(str, Enum):
    SYSTEM_DEFAULT = "system_default"
    CHROME = "chrome"
    EDGE = "edge"
    CUSTOM = "custom"


@dataclass(slots=True)
class AppSettings:
    browser: BrowserChoice = BrowserChoice.CHROME
    custom_browser_path: str = ""
    minimize_to_tray: bool = True
    global_hotkey_enabled: bool = True

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> "AppSettings":
        if not raw or not isinstance(raw, Mapping):
            return cls()

        raw_browser = str(raw.get("browser") or BrowserChoice.CHROME.value).strip().lower()
        browser = _enum_or_none(BrowserChoice, raw_browser) or BrowserChoice.CHROME

        return cls(
            browser=browser,
            custom_browser_path=str(raw.get("custom_browser_path") or "").strip(),
            minimize_to_tray=bool(raw.get("minimize_to_tray", True)),
            global_hotkey_enabled=bool(raw.get("global_hotkey_enabled", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "browser": self.browser.value,
            "custom_browser_path": self.custom_browser_path,
            "minimize_to_tray": self.minimize_to_tray,
            "global_hotkey_enabled": self.global_hotkey_enabled,
        }


@dataclass(slots=True)
class ScenarioStep:
    item_id: str
    delay_seconds: float = 0.0

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ScenarioStep":
        item_id = str(raw.get("item_id") or "").strip()
        if not item_id:
            raise ValueError("Scenario step is missing an item_id.")

        try:
            delay_seconds = max(0.0, float(raw.get("delay_seconds", 0.0)))
        except (TypeError, ValueError):
            delay_seconds = 0.0

        return cls(item_id=item_id, delay_seconds=delay_seconds)

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "delay_seconds": self.delay_seconds}


@dataclass(slots=True)
class Scenario:
    id: str
    name: str
    steps: list[ScenarioStep] = field(default_factory=list)

    @classmethod
    def create(cls, *, name: str, steps: list[ScenarioStep] | None = None) -> "Scenario":
        return cls(id=str(uuid.uuid4()), name=name.strip(), steps=list(steps or []))

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Scenario":
        name = str(raw.get("name") or "").strip()
        if not name:
            raise ValueError("Scenario is missing a name.")

        raw_steps = raw.get("steps")
        steps: list[ScenarioStep] = []
        if isinstance(raw_steps, list):
            for raw_step in raw_steps:
                if isinstance(raw_step, Mapping):
                    steps.append(ScenarioStep.from_dict(raw_step))

        return cls(
            id=str(raw.get("id") or uuid.uuid4()),
            name=name,
            steps=steps,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(slots=True)
class AppConfig:
    launcher_items: list["LauncherItem"]
    ui_state: UiState = field(default_factory=UiState)
    scenarios: list[Scenario] = field(default_factory=list)
    app_settings: AppSettings = field(default_factory=AppSettings)


@dataclass(slots=True)
class LauncherItem:
    id: str
    title: str
    description: str
    type: LauncherType
    target: str
    script: str
    script_type: ScriptType = ScriptType.NONE
    run_mode: RunMode = RunMode.TARGET_THEN_SCRIPT
    icon: str | None = None
    enabled: bool = True

    @classmethod
    def create(
        cls,
        *,
        title: str,
        description: str,
        type: LauncherType,
        target: str,
        script: str,
        script_type: ScriptType = ScriptType.NONE,
        run_mode: RunMode = RunMode.TARGET_THEN_SCRIPT,
        icon: str | None = None,
        enabled: bool = True,
    ) -> "LauncherItem":
        return cls(
            id=str(uuid.uuid4()),
            title=title.strip(),
            description=description.strip(),
            type=type,
            target=target.strip(),
            script=script.strip(),
            script_type=script_type,
            run_mode=run_mode,
            icon=icon.strip() if icon else None,
            enabled=enabled,
        )

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "LauncherItem":
        item_id = str(raw.get("id") or uuid.uuid4())
        title = str(raw.get("title") or "").strip()
        description = str(raw.get("description") or "").strip()
        type_value = str(raw.get("type") or "").strip().lower()
        target = str(raw.get("target") or "").strip()
        script = str(raw.get("script") or "").strip()
        script_type_value = str(raw.get("script_type") or "").strip().lower()
        run_mode_value = str(raw.get("run_mode") or RunMode.TARGET_THEN_SCRIPT.value).strip().lower()
        icon_value = str(raw.get("icon") or "").strip() or None
        enabled = bool(raw.get("enabled", True))

        if not title:
            raise ValueError("Launcher item is missing a title.")
        launcher_type = _enum_or_none(LauncherType, type_value)
        if launcher_type is None:
            raise ValueError(f"Unsupported launcher type: {type_value!r}")
        if script_type_value:
            script_type = _enum_or_none(ScriptType, script_type_value)
            if script_type is None:
                raise ValueError(f"Unsupported script type: {script_type_value!r}")
        else:
            script_type = ScriptType.BUILT_IN_ACTION if script else ScriptType.NONE
        run_mode = _enum_or_none(RunMode, run_mode_value)
        if run_mode is None:
            raise ValueError(f"Unsupported run mode: {run_mode_value!r}")
        if not target and run_mode is not RunMode.SCRIPT_ONLY:
            raise ValueError("Launcher item is missing a target.")
        if not script and run_mode in {RunMode.TARGET_THEN_SCRIPT, RunMode.SCRIPT_ONLY}:
            raise ValueError("Launcher item is missing a script for the selected run mode.")

        return cls(
            id=item_id,
            title=title,
            description=description,
            type=launcher_type,
            target=target,
            script=script,
            script_type=script_type,
            run_mode=run_mode,
            icon=icon_value,
            enabled=enabled,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "target": self.target,
            "script": self.script_name,
            "script_type": self.script_type.value,
            "run_mode": self.run_mode.value,
            "icon": self.icon or "",
            "enabled": self.enabled,
        }

    @property
    def type_label(self) -> str:
        return self.type.value.upper()

    @property
    def run_mode_label(self) -> str:
        labels = {
            RunMode.TARGET_ONLY: "Target Only",
            RunMode.TARGET_THEN_SCRIPT: "Target + Script",
            RunMode.SCRIPT_ONLY: "Script Only",
        }
        return labels[self.run_mode]

    @property
    def script_type_label(self) -> str:
        labels = {
            ScriptType.NONE: "None",
            ScriptType.BUILT_IN_ACTION: "Built-in Action",
            ScriptType.PYTHON_FILE: "Python File",
        }
        return labels[self.script_type]

    @property
    def script_name(self) -> str:
        return self.script.strip()

    def matches_query(self, query: str) -> bool:
        query = query.strip().lower()
        if not query:
            return True
        haystack = " ".join((self.title, self.description, self.target, self.script))
        return query in haystack.lower()
