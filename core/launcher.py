from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence
import webbrowser

from core.action_dispatcher import ActionDispatcher
from core.models import AppSettings, BrowserChoice, LauncherItem, LauncherType, RunMode, ScriptType
from core.paths import AppPaths
from core.windows_shortcuts import SUPPORTED_EXECUTABLE_DROP_SUFFIXES, supported_target_summary


@dataclass(slots=True)
class ExecutionResult:
    success: bool
    message: str


@dataclass(slots=True)
class ItemExecutionReport:
    item: LauncherItem
    target_result: ExecutionResult
    action_result: ExecutionResult

    @property
    def success(self) -> bool:
        return self.target_result.success and self.action_result.success


class LauncherService:
    """Execute launcher targets and then run the mapped Python action."""

    def __init__(
        self,
        logger: logging.Logger,
        dispatcher: ActionDispatcher,
        app_paths: AppPaths | None = None,
    ) -> None:
        self.logger = logger
        self.dispatcher = dispatcher
        self.app_paths = app_paths
        self.app_settings = AppSettings()
        self._chrome_path = self._find_chrome()
        self._edge_path = self._find_edge()

        if self._chrome_path:
            self.logger.info("Detected Chrome at %s", self._chrome_path)
        else:
            self.logger.info("Chrome not found. URL items will open in the default browser.")
        if self._edge_path:
            self.logger.info("Detected Edge at %s", self._edge_path)

    def launch_target(self, item: LauncherItem) -> ExecutionResult:
        if item.type is LauncherType.URL:
            return self._launch_url(item)
        if item.type is LauncherType.EXE:
            return self._launch_exe(item)

        message = f"Unsupported launcher type: {item.type!r}"
        self.logger.error(message)
        return ExecutionResult(False, message)

    def run_action(self, item: LauncherItem) -> ExecutionResult:
        script_name = item.script_name
        if not script_name:
            return ExecutionResult(True, "No script configured.")

        if item.script_type is ScriptType.NONE:
            return ExecutionResult(True, "No script configured.")
        if item.script_type is ScriptType.BUILT_IN_ACTION:
            success = self.dispatcher.dispatch(script_name, item)
            message = f"Action '{script_name}' {'completed' if success else 'failed'}"
            return ExecutionResult(success, message)
        if item.script_type is ScriptType.PYTHON_FILE:
            return self._run_python_file(item, script_name)

        return ExecutionResult(False, f"Unsupported script type: {item.script_type.value}")

    def execute_item(self, item: LauncherItem) -> ItemExecutionReport:
        if item.run_mode is RunMode.TARGET_ONLY:
            target_result = self.launch_target(item)
            action_result = ExecutionResult(True, "Script skipped by run mode.")
        elif item.run_mode is RunMode.SCRIPT_ONLY:
            target_result = ExecutionResult(True, "Target skipped by run mode.")
            action_result = self.run_action(item)
        else:
            target_result = self.launch_target(item)
            action_result = self.run_action(item)
        return ItemExecutionReport(
            item=item,
            target_result=target_result,
            action_result=action_result,
        )

    def execute_group(self, items: Sequence[LauncherItem]) -> list[ItemExecutionReport]:
        reports: list[ItemExecutionReport] = []
        for item in items:
            reports.append(self.execute_item(item))
        return reports

    def _launch_url(self, item: LauncherItem) -> ExecutionResult:
        target = item.target.strip()
        if not target:
            message = f"URL target is empty for '{item.title}'"
            self.logger.warning(message)
            return ExecutionResult(False, message)

        self.logger.info("Launching URL target for '%s': %s", item.title, target)

        browser_command = self._resolve_browser_command()
        if browser_command:
            browser_path = Path(browser_command[0])
            browser_name = browser_path.stem
            try:
                subprocess.Popen([*browser_command, target], cwd=str(browser_path.parent))
            except OSError:
                self.logger.exception("Browser launch failed for '%s'", item.title)
                return ExecutionResult(False, f"Failed to open URL in {browser_name}: {target}")

            self.logger.info("URL launch succeeded for '%s' via %s", item.title, browser_name)
            return ExecutionResult(True, f"Opened URL in {browser_name}: {target}")

        self.logger.info("Opening '%s' in the default browser.", item.title)
        try:
            opened = webbrowser.open(target)
        except Exception:
            self.logger.exception("Default browser launch failed for '%s'", item.title)
            opened = False

        if not opened:
            message = f"Failed to open URL in the default browser: {target}"
            self.logger.error(message)
            return ExecutionResult(False, message)

        self.logger.info("URL launch succeeded for '%s' via default browser", item.title)
        return ExecutionResult(True, f"Opened URL in default browser: {target}")

    def _launch_exe(self, item: LauncherItem) -> ExecutionResult:
        raw_target = item.target.strip()
        if not raw_target:
            message = f"Application target is empty for '{item.title}'"
            self.logger.warning(message)
            return ExecutionResult(False, message)

        target_path = Path(os.path.expandvars(raw_target)).expanduser()
        try:
            target_path = target_path.resolve(strict=False)
        except OSError:
            pass

        suffix = target_path.suffix.lower()
        if suffix not in SUPPORTED_EXECUTABLE_DROP_SUFFIXES:
            message = (
                f"Unsupported application target '{target_path}'. "
                f"Supported types: {supported_target_summary()}"
            )
            self.logger.warning(message)
            return ExecutionResult(False, message)

        if not target_path.exists():
            message = f"Application target not found: {target_path}"
            self.logger.warning(message)
            return ExecutionResult(False, message)

        if suffix in {".exe", ".com"}:
            self.logger.info("Launching executable target for '%s': %s", item.title, target_path)
            try:
                subprocess.Popen([str(target_path)], cwd=str(target_path.parent))
            except OSError:
                self.logger.exception("Executable launch failed for '%s'", item.title)
                return ExecutionResult(False, f"Failed to launch executable: {target_path}")

            self.logger.info("Executable launch succeeded for '%s'", item.title)
            return ExecutionResult(True, f"Launched executable: {target_path}")

        if suffix == ".ps1":
            powershell_command = shutil.which("powershell.exe") or shutil.which("powershell")
            if not powershell_command:
                message = "PowerShell is required to launch .ps1 targets, but powershell.exe was not found."
                self.logger.error(message)
                return ExecutionResult(False, message)

            self.logger.info("Launching PowerShell target for '%s': %s", item.title, target_path)
            try:
                subprocess.Popen(
                    [powershell_command, "-ExecutionPolicy", "Bypass", "-File", str(target_path)],
                    cwd=str(target_path.parent),
                )
            except OSError:
                self.logger.exception("PowerShell target launch failed for '%s'", item.title)
                return ExecutionResult(False, f"Failed to launch PowerShell target: {target_path}")

            self.logger.info("PowerShell target launch succeeded for '%s'", item.title)
            return ExecutionResult(True, f"Launched PowerShell target: {target_path}")

        self.logger.info("Launching shell-handled target for '%s': %s", item.title, target_path)
        try:
            os.startfile(str(target_path))
        except OSError:
            self.logger.exception("Shell-handled target launch failed for '%s'", item.title)
            return ExecutionResult(False, f"Failed to open target: {target_path}")

        self.logger.info("Shell-handled target launch succeeded for '%s'", item.title)
        return ExecutionResult(True, f"Opened target: {target_path}")

    def _resolve_browser_command(self) -> list[str] | None:
        """Return the browser launch command per settings, or None for the system default."""
        choice = self.app_settings.browser

        if choice is BrowserChoice.SYSTEM_DEFAULT:
            return None

        if choice is BrowserChoice.CUSTOM:
            custom_raw = self.app_settings.custom_browser_path.strip()
            if custom_raw:
                custom_path = Path(os.path.expandvars(custom_raw)).expanduser()
                if custom_path.exists():
                    return [str(custom_path)]
                self.logger.warning("Custom browser not found: %s. Falling back to default.", custom_path)
            return None

        if choice is BrowserChoice.EDGE:
            edge_path = self._edge_path or self._find_edge()
            if edge_path:
                self._edge_path = edge_path
                return [str(edge_path), "--new-tab"]
            self.logger.warning("Edge not found. Falling back to the default browser.")
            return None

        chrome_path = self._chrome_path or self._find_chrome()
        if chrome_path:
            self._chrome_path = chrome_path
            return [str(chrome_path), "--new-tab"]
        return None

    def _find_edge(self) -> Path | None:
        candidates: list[Path] = []

        path_hit = shutil.which("msedge") or shutil.which("msedge.exe")
        if path_hit:
            candidates.append(Path(path_hit))

        for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            root = os.environ.get(env_name)
            if not root:
                continue
            candidates.append(Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe")

        seen: set[str] = set()
        for candidate in candidates:
            normalized = str(candidate).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            if candidate.exists():
                return candidate

        return None

    def _find_chrome(self) -> Path | None:
        candidates: list[Path] = []

        path_hit = shutil.which("chrome") or shutil.which("chrome.exe")
        if path_hit:
            candidates.append(Path(path_hit))

        for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            root = os.environ.get(env_name)
            if not root:
                continue
            candidates.append(Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe")

        seen: set[str] = set()
        for candidate in candidates:
            normalized = str(candidate).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            if candidate.exists():
                return candidate

        return None

    def _run_python_file(self, item: LauncherItem, script_name: str) -> ExecutionResult:
        script_path = Path(os.path.expandvars(script_name)).expanduser()
        try:
            script_path = script_path.resolve(strict=False)
        except OSError:
            pass

        if script_path.suffix.lower() != ".py":
            message = f"Python script must be a .py file: {script_path}"
            self.logger.warning(message)
            return ExecutionResult(False, message)

        if not script_path.exists():
            message = f"Python script not found: {script_path}"
            self.logger.warning(message)
            return ExecutionResult(False, message)

        python_command = self._resolve_python_command()
        if not python_command:
            message = "No Python interpreter was found for running external scripts."
            self.logger.error(message)
            return ExecutionResult(False, message)

        env = os.environ.copy()
        env["ORBIT_PANEL_ITEM_ID"] = item.id
        env["ORBIT_PANEL_ITEM_TITLE"] = item.title
        env["ORBIT_PANEL_ITEM_TYPE"] = item.type.value
        env["ORBIT_PANEL_ITEM_TARGET"] = item.target
        env["ORBIT_PANEL_ITEM_ENABLED"] = "true" if item.enabled else "false"
        env["ORBIT_PANEL_RUN_MODE"] = item.run_mode.value
        env["ORBIT_PANEL_SCRIPT_TYPE"] = item.script_type.value
        env["ORBIT_PANEL_SCRIPT_VALUE"] = item.script_name
        if self.app_paths is not None:
            env["ORBIT_PANEL_BASE_DIR"] = str(self.app_paths.base_dir)
            env["ORBIT_PANEL_RUNTIME_DIR"] = str(self.app_paths.runtime_dir)
            env["ORBIT_PANEL_CONFIG_FILE"] = str(self.app_paths.config_file)
            env["ORBIT_PANEL_LOG_DIR"] = str(self.app_paths.logs_dir)
            helpers_dir = self.app_paths.base_dir / "scripts"
            if helpers_dir.exists():
                env["ORBIT_PANEL_HELPERS_DIR"] = str(helpers_dir)
        env["ORBIT_PANEL_ITEM_CONTEXT"] = json.dumps(
            {
                "id": item.id,
                "title": item.title,
                "type": item.type.value,
                "target": item.target,
                "run_mode": item.run_mode.value,
                "script_type": item.script_type.value,
                "script": item.script_name,
                "enabled": item.enabled,
            },
            ensure_ascii=False,
        )

        command = [*python_command, str(script_path)]
        self.logger.info("Running Python script for '%s': %s", item.title, command)
        try:
            subprocess.Popen(
                command,
                cwd=str(script_path.parent),
                env=env,
            )
        except OSError:
            self.logger.exception("Python script launch failed for '%s'", item.title)
            return ExecutionResult(False, f"Failed to run Python script: {script_path}")

        return ExecutionResult(True, f"Started Python script: {script_path}")

    def _resolve_python_command(self) -> list[str] | None:
        current_executable = Path(sys.executable)
        current_name = current_executable.name.lower()
        if current_name in {"python.exe", "pythonw.exe"} and current_executable.exists():
            return [str(current_executable)]

        for candidate in ("pyw", "py", "pythonw", "python", "python3"):
            hit = shutil.which(candidate)
            if not hit:
                continue
            command = [hit]
            if Path(hit).stem.lower() in {"py", "pyw"}:
                command.append("-3")
            return command

        return None
