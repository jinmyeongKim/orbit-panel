from __future__ import annotations

import sys

from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from core.action_dispatcher import ActionDispatcher
from core.config_loader import ConfigLoader
from core.launcher import LauncherService
from core.logger import LogStore, configure_logging
from core.paths import AppPaths
from core.windows_diagnostics import log_drag_and_drop_diagnostics, set_app_user_model_id
from ui.main_window import MainWindow


def _build_app_font() -> QFont:
    available_families = set(QFontDatabase.families())

    for family in ("Pretendard", "Malgun Gothic", "Segoe UI Variable Text", "Segoe UI"):
        if family in available_families:
            font = QFont(family, 10)
            font.setStyleStrategy(QFont.PreferAntialias)
            return font

    fallback_font = QFont()
    fallback_font.setPointSize(10)
    fallback_font.setStyleStrategy(QFont.PreferAntialias)
    return fallback_font


def main() -> int:
    """Start the Orbit Panel desktop application."""
    app_paths = AppPaths.discover()
    app_paths.ensure_runtime_dirs()

    log_store = LogStore()
    logger = configure_logging(log_store, app_paths.log_file)
    logger.info("Application starting")
    logger.info("Runtime directory: %s", app_paths.runtime_dir)
    logger.info("Config file: %s", app_paths.config_file)
    set_app_user_model_id("OrbitPanel.Desktop", logger)

    app = QApplication(sys.argv)
    app.setApplicationName("Orbit Panel")
    app.setOrganizationName("Orbit Panel")
    app.setStyle("Fusion")
    app.setFont(_build_app_font())

    app_icon = QIcon(str(app_paths.app_icon_file))
    logger.info("App icon path: %s", app_paths.app_icon_file)
    logger.info("App icon exists: %s", app_paths.app_icon_file.exists())
    logger.info("App icon loaded: %s", not app_icon.isNull())
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    log_drag_and_drop_diagnostics(logger)

    config_loader = ConfigLoader(
        app_paths.config_file,
        logger,
        legacy_config_path=app_paths.legacy_config_file,
    )
    dispatcher = ActionDispatcher(logger)
    launcher_service = LauncherService(logger, dispatcher, app_paths=app_paths)

    window = MainWindow(
        config_loader=config_loader,
        launcher_service=launcher_service,
        dispatcher=dispatcher,
        log_store=log_store,
        logger=logger,
        app_paths=app_paths,
    )
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.show()
    if not app_icon.isNull() and window.windowHandle() is not None:
        window.windowHandle().setIcon(app_icon)

    exit_code = app.exec()
    logger.info("Application shutting down")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
