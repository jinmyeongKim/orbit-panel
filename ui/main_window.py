from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.action_dispatcher import ActionDispatcher
from core.config_loader import ConfigLoader
from core.launcher import LauncherService
from core.logger import LogStore
from core.models import AppConfig, DialogDraft, LauncherItem, LauncherType, RunMode, ScriptType, UiState
from core.paths import AppPaths
from core.windows_shortcuts import (
    is_supported_executable_drop_path,
    resolve_executable_drop_target,
    supported_target_summary,
)
from ui.add_edit_dialog import AddEditLauncherDialog
from ui.group_panel import LauncherGroupPanel
from ui.styles import APP_STYLESHEET


class ExternalDropOverlay(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._target_visible = False
        self._fade_effect = QGraphicsOpacityEffect(self)
        self._fade_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._fade_effect)
        self._fade_animation = QPropertyAnimation(self._fade_effect, b"opacity", self)
        self._fade_animation.setDuration(180)
        self._fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(56, 56, 56, 56)
        layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("DropOverlayCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card.setMaximumWidth(680)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 26)
        card_layout.setSpacing(12)

        eyebrow = QLabel("READY TO ADD")
        eyebrow.setObjectName("DropOverlayEyebrow")

        title = QLabel("Drop app target here")
        title.setObjectName("DropOverlayTitle")
        title.setWordWrap(True)
        title.setMinimumHeight(44)

        subtitle = QLabel("Added to the bottom of the EXE group and saved immediately.")
        subtitle.setObjectName("DropOverlaySubtitle")
        subtitle.setWordWrap(True)
        subtitle.setMinimumHeight(28)

        card_layout.addWidget(eyebrow)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        layout.addStretch(1)
        layout.addWidget(card, 0, Qt.AlignCenter)
        layout.addStretch(1)

    def set_visible_animated(self, visible: bool) -> None:
        if visible == self._target_visible and (
            (visible and self.isVisible()) or (not visible and not self.isVisible())
        ):
            return

        self._target_visible = visible
        self._fade_animation.stop()

        if visible:
            if not self.isVisible():
                self.show()
            self.raise_()
            self._fade_animation.setStartValue(self._fade_effect.opacity())
            self._fade_animation.setEndValue(1.0)
            self._fade_animation.start()
            return

        if not self.isVisible():
            return

        self._fade_animation.setStartValue(self._fade_effect.opacity())
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.finished.connect(self._hide_if_transparent, Qt.ConnectionType.SingleShotConnection)
        self._fade_animation.start()

    def _hide_if_transparent(self) -> None:
        if self._fade_effect.opacity() <= 0.01:
            self.hide()


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        config_loader: ConfigLoader,
        launcher_service: LauncherService,
        dispatcher: ActionDispatcher,
        log_store: LogStore,
        logger: logging.Logger,
        app_paths: AppPaths,
    ) -> None:
        super().__init__()
        self.config_loader = config_loader
        self.launcher_service = launcher_service
        self.dispatcher = dispatcher
        self.log_store = log_store
        self.logger = logger
        self.app_paths = app_paths

        self._items: list[LauncherItem] = []
        self._filtered_items: list[LauncherItem] = []
        self._selected_item_ids: set[str] = set()
        self._ui_state = UiState()
        self._last_status_message = ""
        self._external_drop_targets: set[int] = set()

        self.setWindowTitle("Orbit Panel")
        self.setMinimumSize(1280, 860)
        self.resize(1460, 940)
        self.setAcceptDrops(True)
        self.setStyleSheet(APP_STYLESHEET)

        self._build_ui()
        self._load_items()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("RootWidget")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(18)

        hero_panel = QFrame()
        hero_panel.setObjectName("HeroPanel")
        hero_layout = QHBoxLayout(hero_panel)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(20)

        title_column = QVBoxLayout()
        title_column.setSpacing(8)

        eyebrow = QLabel("BATCH APP / URL LAUNCHER")
        eyebrow.setObjectName("HeroEyebrow")

        hero_title = QLabel("Orbit Panel")
        hero_title.setObjectName("HeroTitle")

        hero_subtitle = QLabel(
            "Keep one URL list and one EXE list. Drag rows to set order, then add EXEs from the last slot card."
        )
        hero_subtitle.setObjectName("HeroSubtitle")
        hero_subtitle.setWordWrap(True)

        title_column.addWidget(eyebrow)
        title_column.addWidget(hero_title)
        title_column.addWidget(hero_subtitle)

        hero_layout.addLayout(title_column, 1)

        hero_actions = QVBoxLayout()
        hero_actions.setSpacing(10)

        self.run_all_button = QPushButton("Run All")
        self.run_all_button.setObjectName("PrimaryButton")
        self.run_all_button.clicked.connect(self._run_all_items)

        self.run_selected_button = QPushButton("Run Selected")
        self.run_selected_button.setObjectName("FlatActionButton")
        self.run_selected_button.clicked.connect(self._run_selected_items)

        hero_actions.addStretch(1)
        hero_actions.addWidget(self.run_selected_button, 0, Qt.AlignRight)
        hero_actions.addWidget(self.run_all_button, 0, Qt.AlignRight)
        hero_actions.addStretch(1)

        hero_layout.addLayout(hero_actions, 0)

        self.groups_container = QWidget()
        self.groups_container.setObjectName("GroupsContainer")

        groups_row = QHBoxLayout(self.groups_container)
        groups_row.setSpacing(18)
        groups_row.setContentsMargins(0, 0, 0, 0)

        self.url_group_panel = LauncherGroupPanel(
            group_type=LauncherType.URL,
            title="URL Group",
            subtitle="URLs are opened in the visible order.",
        )
        self.exe_group_panel = LauncherGroupPanel(
            group_type=LauncherType.EXE,
            title="EXE Group",
            subtitle="Windows launch targets are opened in the visible order.",
        )

        self.url_group_panel.add_requested.connect(self._open_add_dialog)
        self.url_group_panel.quick_url_submitted.connect(self._add_url_from_input)
        self.url_group_panel.run_all_requested.connect(self._run_group)
        self.url_group_panel.run_item_requested.connect(self._run_single_item)
        self.url_group_panel.selection_changed.connect(self._set_item_selected)
        self.url_group_panel.edit_item_requested.connect(self._edit_card)
        self.url_group_panel.delete_item_requested.connect(self._delete_card)
        self.url_group_panel.item_order_changed.connect(self._reorder_group)
        self.url_group_panel.files_dropped.connect(self._handle_exe_drop_paths)

        self.exe_group_panel.run_all_requested.connect(self._run_group)
        self.exe_group_panel.run_item_requested.connect(self._run_single_item)
        self.exe_group_panel.selection_changed.connect(self._set_item_selected)
        self.exe_group_panel.edit_item_requested.connect(self._edit_card)
        self.exe_group_panel.delete_item_requested.connect(self._delete_card)
        self.exe_group_panel.item_order_changed.connect(self._reorder_group)
        self.exe_group_panel.files_dropped.connect(self._handle_exe_drop_paths)

        groups_row.addWidget(self.url_group_panel, 1)
        groups_row.addWidget(self.exe_group_panel, 1)

        self.drop_overlay = ExternalDropOverlay(self.groups_container)

        root_layout.addWidget(hero_panel)
        root_layout.addWidget(self.groups_container, 1)

        self.setCentralWidget(root)
        self._register_external_drop_watch_tree(root)

    def _load_items(self) -> None:
        self.logger.info("Loading launcher items from JSON")
        config = self.config_loader.load_config()
        self._items = config.launcher_items
        self._ui_state = config.ui_state
        self._restore_ui_state()
        self._set_status(f"Loaded {len(self._items)} Orbit Panel items.")
        self._apply_filter()

    def _apply_filter(self, *_args) -> None:
        query = ""
        self._filtered_items = [item for item in self._items if item.matches_query(query)]
        self._render_groups()
        self._update_metrics()

    def _render_groups(self) -> None:
        existing_ids = {item.id for item in self._items}
        self._selected_item_ids.intersection_update(existing_ids)

        url_items = [item for item in self._filtered_items if item.type is LauncherType.URL]
        exe_items = [item for item in self._filtered_items if item.type is LauncherType.EXE]

        self.url_group_panel.set_items(url_items, selected_ids=self._selected_item_ids)
        self.exe_group_panel.set_items(exe_items, selected_ids=self._selected_item_ids)
        self._register_external_drop_watch_tree(self.groups_container)
        self._update_drop_overlay_geometry()
        self._update_selection_controls()

        self.logger.info(
            "Rendered groups: %s URL item(s), %s EXE item(s)",
            len(url_items),
            len(exe_items),
        )

    def _update_metrics(self) -> None:
        return

    def _update_selection_controls(self) -> None:
        selected_count = len(self._selected_item_ids)
        self.run_selected_button.setText(
            f"Run Selected ({selected_count})" if selected_count else "Run Selected"
        )
        self.run_selected_button.setEnabled(selected_count > 0)

    def _set_status(self, message: str) -> None:
        self._last_status_message = message
        self.logger.info("Status: %s", message)

    def _restore_ui_state(self) -> None:
        width = max(self.minimumWidth(), self._ui_state.window_width)
        height = max(self.minimumHeight(), self._ui_state.window_height)
        self.resize(width, height)

        if self._ui_state.window_x is not None and self._ui_state.window_y is not None:
            self.move(self._ui_state.window_x, self._ui_state.window_y)

        self.url_group_panel.quick_url_input.setText(self._ui_state.last_url_input)

        if self._ui_state.window_maximized:
            self.setWindowState(self.windowState() | Qt.WindowMaximized)

        self.logger.info("Restored UI state from JSON")

    def _capture_ui_state(self) -> UiState:
        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()

        return UiState(
            window_x=geometry.x(),
            window_y=geometry.y(),
            window_width=max(self.minimumWidth(), geometry.width()),
            window_height=max(self.minimumHeight(), geometry.height()),
            window_maximized=self.isMaximized(),
            last_url_input=self.url_group_panel.quick_url_input.text().strip(),
            dialog_draft=self._ui_state.dialog_draft,
        )

    def _register_external_drop_watch_tree(self, widget: QWidget) -> None:
        widget_id = id(widget)
        if widget_id not in self._external_drop_targets:
            widget.setAcceptDrops(True)
            widget.installEventFilter(self)
            self._external_drop_targets.add(widget_id)

        for child in widget.findChildren(QWidget):
            child_id = id(child)
            if child_id in self._external_drop_targets:
                continue
            child.setAcceptDrops(True)
            child.installEventFilter(self)
            self._external_drop_targets.add(child_id)

    def _contains_external_exe_drop(self, event) -> bool:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return False

        return any(
            url.isLocalFile() and is_supported_executable_drop_path(Path(url.toLocalFile()))
            for url in mime_data.urls()
        )

    def _extract_external_drop_paths(self, event) -> list[Path]:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return []

        return [Path(url.toLocalFile()) for url in mime_data.urls() if url.isLocalFile()]

    def _set_drop_overlay_visible(self, visible: bool) -> None:
        self._update_drop_overlay_geometry()
        self.drop_overlay.set_visible_animated(visible)

    def _update_drop_overlay_geometry(self) -> None:
        if not hasattr(self, "groups_container") or not hasattr(self, "drop_overlay"):
            return

        self.drop_overlay.setGeometry(self.groups_container.rect())

    def _open_add_dialog(self, group_type_value: str | None = None) -> None:
        preset_type = LauncherType(group_type_value) if group_type_value else None
        dialog = AddEditLauncherDialog(
            available_actions=self.dispatcher.available_actions(),
            draft=self._ui_state.dialog_draft,
            preset_type=preset_type,
            type_locked=bool(preset_type),
            parent=self,
        )
        dialog_result = dialog.exec()
        self._ui_state.dialog_draft = dialog.draft_state()
        if dialog_result != QDialog.Accepted:
            return

        item = dialog.result_item()
        if item is None:
            return

        self._items.append(item)
        self._items = self._normalize_item_order(self._items)
        self.logger.info("Orbit Panel item added: %s", item.title)
        if self._save_items():
            self._set_status(f"Added '{item.title}' to the {item.type_label} group.")
            self._apply_filter()

    def _add_url_from_input(self, raw_url: str) -> None:
        target = raw_url.strip()
        if not target:
            return

        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        parsed = urlparse(target)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            QMessageBox.warning(self, "Invalid URL", "Enter a valid HTTP or HTTPS URL.")
            return

        item = LauncherItem.create(
            title=self._suggest_url_title(target),
            description="",
            type=LauncherType.URL,
            target=target,
            script="",
            script_type=ScriptType.NONE,
            run_mode=RunMode.TARGET_ONLY,
            icon=None,
            enabled=True,
        )
        self._items.append(item)
        self._items = self._normalize_item_order(self._items)
        self.logger.info("URL item added from quick input: %s", target)

        if self._save_items():
            self._set_status(f"Added URL '{target}'.")
            self._apply_filter()

    def _edit_card(self, item_id: str) -> None:
        item = self._find_item(item_id)
        if item is None:
            return

        dialog = AddEditLauncherDialog(
            available_actions=self.dispatcher.available_actions(),
            item=item,
            parent=self,
        )
        dialog_result = dialog.exec()
        self._ui_state.dialog_draft = dialog.draft_state()
        if dialog_result != QDialog.Accepted:
            return

        result_item = dialog.result_item()
        if result_item is None:
            return

        for index, existing_item in enumerate(self._items):
            if existing_item.id == item_id:
                self._items[index] = result_item
                break

        self._items = self._normalize_item_order(self._items)

        self.logger.info("Orbit Panel item edited: %s", result_item.title)
        if self._save_items():
            self._set_status(f"Updated '{result_item.title}'.")
            self._apply_filter()

    def _delete_card(self, item_id: str) -> None:
        item = self._find_item(item_id)
        if item is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Orbit Panel Item",
            f"Delete '{item.title}' from the {item.type_label} group?\n\nThis change is saved immediately.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self._selected_item_ids.discard(item.id)
        self._items = [existing_item for existing_item in self._items if existing_item.id != item_id]
        self.logger.info("Orbit Panel item deleted: %s", item.title)
        if self._save_items():
            self._set_status(f"Deleted '{item.title}'.")
            self._apply_filter()

    def _save_items(self) -> bool:
        self._ui_state = self._capture_ui_state()
        try:
            self.config_loader.save_config(
                AppConfig(launcher_items=list(self._items), ui_state=self._ui_state)
            )
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save launcher_items.json.\n\n{exc}",
            )
            self.logger.exception("Settings save failed")
            self._set_status("Save failed. See the log panel for details.")
            return False
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        self.logger.info("Close requested. Persisting Orbit Panel state to JSON.")
        if not self._save_items():
            event.ignore()
            return

        super().closeEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_drop_overlay_geometry()

    def dragEnterEvent(self, event) -> None:
        if self._contains_external_exe_drop(event):
            self._set_drop_overlay_visible(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self._contains_external_exe_drop(event):
            self._set_drop_overlay_visible(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._set_drop_overlay_visible(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        if self._contains_external_exe_drop(event):
            self._set_drop_overlay_visible(False)
            self._handle_exe_drop_paths(self._extract_external_drop_paths(event))
            event.acceptProposedAction()
            return
        event.ignore()

    def eventFilter(self, watched, event) -> bool:
        event_type = event.type()
        if event_type in {QEvent.DragEnter, QEvent.DragMove}:
            if self._contains_external_exe_drop(event):
                self._set_drop_overlay_visible(True)
                event.acceptProposedAction()
                return True
        elif event_type == QEvent.DragLeave:
            if watched in {self, self.groups_container, self.centralWidget()}:
                self._set_drop_overlay_visible(False)
        elif event_type == QEvent.Drop:
            if self._contains_external_exe_drop(event):
                self._set_drop_overlay_visible(False)
                self._handle_exe_drop_paths(self._extract_external_drop_paths(event))
                event.acceptProposedAction()
                return True

        return super().eventFilter(watched, event)

    def _run_single_item(self, item_id: str) -> None:
        item = self._find_item(item_id)
        if item is None:
            return

        self.logger.info("Manual item run requested: %s (%s)", item.title, item.type.value)
        if not item.enabled:
            self.logger.warning("Ignored run for disabled item '%s'", item.title)
            self._set_status(f"'{item.title}' is disabled.")
            return

        report = self.launcher_service.execute_item(item)
        self._log_item_report(report)
        self._set_status(
            f"Ran '{item.title}' | target: {'ok' if report.target_result.success else 'failed'} | "
            f"action: {'ok' if report.action_result.success else 'failed'}"
        )

    def _run_group(self, group_type_value: str) -> None:
        group_type = LauncherType(group_type_value)
        group_name = "URL group" if group_type is LauncherType.URL else "EXE group"

        items = [item for item in self._items if item.type is group_type and item.enabled]
        if not items:
            QMessageBox.information(
                self,
                "Nothing to Run",
                f"There are no enabled items in the {group_name}.",
            )
            self.logger.warning("Run All requested for empty or disabled-only %s", group_name)
            self._set_status(f"No enabled items in the {group_name}.")
            return

        self.logger.info("Run All requested for %s with %s enabled item(s)", group_name, len(items))
        reports = self.launcher_service.execute_group(items)

        target_success_count = 0
        action_success_count = 0
        for report in reports:
            self._log_item_report(report)
            target_success_count += int(report.target_result.success)
            action_success_count += int(report.action_result.success)

        self._set_status(
            f"Run All complete for {group_name}: "
            f"{target_success_count}/{len(reports)} targets ok, "
            f"{action_success_count}/{len(reports)} actions ok"
        )

    def _run_all_items(self) -> None:
        items = [item for item in self._items if item.enabled]
        if not items:
            QMessageBox.information(self, "Nothing to Run", "There are no enabled items to run.")
            self.logger.warning("Global Run All requested with no enabled items")
            return

        self.logger.info("Global Run All requested with %s enabled item(s)", len(items))
        reports = self.launcher_service.execute_group(items)

        target_success_count = 0
        action_success_count = 0
        for report in reports:
            self._log_item_report(report)
            target_success_count += int(report.target_result.success)
            action_success_count += int(report.action_result.success)

        self._set_status(
            f"Run All complete: {target_success_count}/{len(reports)} targets ok, "
            f"{action_success_count}/{len(reports)} actions ok"
        )

    def _run_selected_items(self) -> None:
        items = [item for item in self._items if item.id in self._selected_item_ids and item.enabled]
        if not items:
            QMessageBox.information(
                self,
                "Nothing Selected",
                "Select one or more enabled items to run only those entries.",
            )
            self.logger.warning("Run Selected requested with no enabled selected items")
            return

        self.logger.info("Run Selected requested with %s enabled selected item(s)", len(items))
        reports = self.launcher_service.execute_group(items)

        target_success_count = 0
        action_success_count = 0
        for report in reports:
            self._log_item_report(report)
            target_success_count += int(report.target_result.success)
            action_success_count += int(report.action_result.success)

        self._set_status(
            f"Run Selected complete: {target_success_count}/{len(reports)} targets ok, "
            f"{action_success_count}/{len(reports)} actions ok"
        )

    def _reorder_group(self, group_type_value: str, ordered_ids: list[str]) -> None:
        group_type = LauncherType(group_type_value)
        url_items, exe_items = self._split_items_by_group(self._items)
        group_items = url_items if group_type is LauncherType.URL else exe_items
        current_ids = [item.id for item in group_items]

        if ordered_ids == current_ids:
            return

        item_lookup = {item.id: item for item in group_items}
        reordered_items = [item_lookup[item_id] for item_id in ordered_ids if item_id in item_lookup]
        reordered_items.extend(item for item in group_items if item.id not in ordered_ids)

        if group_type is LauncherType.URL:
            url_items = reordered_items
        else:
            exe_items = reordered_items

        self._items = self._merge_group_items(url_items, exe_items)
        self.logger.info("Reordered %s group via drag-and-drop", group_type.value.upper())

        if self._save_items():
            group_label = "URL" if group_type is LauncherType.URL else "EXE"
            self._set_status(f"Updated run order for the {group_label} group.")
            self._apply_filter()
            return

        if group_type is LauncherType.URL:
            self.url_group_panel.reset_reorder_preview()
        else:
            self.exe_group_panel.reset_reorder_preview()

    def _log_item_report(self, report) -> None:
        item = report.item
        if report.target_result.success:
            self.logger.info("Target execution succeeded for '%s': %s", item.title, report.target_result.message)
        else:
            self.logger.warning("Target execution failed for '%s': %s", item.title, report.target_result.message)

        if report.action_result.success:
            self.logger.info("Action execution succeeded for '%s': %s", item.title, report.action_result.message)
        else:
            self.logger.warning("Action execution failed for '%s': %s", item.title, report.action_result.message)

    def _find_item(self, item_id: str) -> LauncherItem | None:
        for item in self._items:
            if item.id == item_id:
                return item
        self.logger.warning("Requested Orbit Panel item was not found: %s", item_id)
        return None

    def _set_item_selected(self, item_id: str, selected: bool) -> None:
        if selected:
            self._selected_item_ids.add(item_id)
            self.logger.info("Selected item: %s", item_id)
        else:
            self._selected_item_ids.discard(item_id)
            self.logger.info("Deselected item: %s", item_id)

        self._update_selection_controls()

    def _split_items_by_group(
        self, items: list[LauncherItem]
    ) -> tuple[list[LauncherItem], list[LauncherItem]]:
        url_items = [item for item in items if item.type is LauncherType.URL]
        exe_items = [item for item in items if item.type is LauncherType.EXE]
        return url_items, exe_items

    def _merge_group_items(
        self, url_items: list[LauncherItem], exe_items: list[LauncherItem]
    ) -> list[LauncherItem]:
        return [*url_items, *exe_items]

    def _normalize_item_order(self, items: list[LauncherItem]) -> list[LauncherItem]:
        url_items, exe_items = self._split_items_by_group(items)
        return self._merge_group_items(url_items, exe_items)

    def _suggest_url_title(self, target: str) -> str:
        parsed = urlparse(target)
        host = parsed.netloc.strip().lower()
        if host.startswith("www."):
            host = host[4:]
        return host or target

    def _handle_exe_drop_paths(self, files: list[Path]) -> None:
        self._set_drop_overlay_visible(False)
        self.logger.info("Drag-and-drop received %s file(s)", len(files))

        exe_files = [path for path in files if is_supported_executable_drop_path(path)]
        rejected_files = [path for path in files if not is_supported_executable_drop_path(path)]

        if rejected_files:
            rejected_list = "\n".join(str(path) for path in rejected_files[:5])
            QMessageBox.warning(
                self,
                "Unsupported Drop",
                f"Only supported Windows launch targets can be added ({supported_target_summary()}).\n\nRejected:\n{rejected_list}",
            )
            self.logger.warning("Rejected unsupported launch-target payload: %s", rejected_list)

        added_count = 0
        for exe_path in exe_files:
            if self._add_dropped_exe(exe_path):
                added_count += 1

        if added_count:
            self._set_status(f"Added {added_count} item(s) to the EXE group.")
            self._apply_filter()

    def _add_dropped_exe(self, file_path: Path) -> bool:
        resolved_path = resolve_executable_drop_target(file_path, self.logger)
        if resolved_path is None:
            QMessageBox.warning(
                self,
                "Drop Error",
                f"Could not resolve this file to an application target:\n{file_path}",
            )
            self.logger.warning("Rejected unresolved application drop: %s", file_path)
            return False

        for existing_item in self._items:
            if existing_item.type is not LauncherType.EXE:
                continue

            current_target = Path(os.path.expandvars(existing_item.target)).expanduser()
            try:
                normalized_target = current_target.resolve(strict=False)
            except OSError:
                normalized_target = current_target

            if normalized_target == resolved_path:
                QMessageBox.information(
                    self,
                    "Already Added",
                    f"This executable is already registered:\n{resolved_path}",
                )
                self.logger.warning("Skipped duplicate dropped EXE: %s", resolved_path)
                return False

        item = LauncherItem.create(
            title=file_path.stem or resolved_path.stem,
            description=f"Added from drag-and-drop for {resolved_path.name}.",
            type=LauncherType.EXE,
            target=str(resolved_path),
            script="",
            script_type=ScriptType.NONE,
            run_mode=RunMode.TARGET_ONLY,
            icon=str(resolved_path),
            enabled=True,
        )
        self._items.append(item)
        self._items = self._normalize_item_order(self._items)
        self.logger.info("Created EXE group item from drag-and-drop: %s", resolved_path)

        if not self._save_items():
            self._items = [existing_item for existing_item in self._items if existing_item.id != item.id]
            return False

        return True
