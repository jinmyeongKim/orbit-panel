from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QParallelAnimationGroup, QPropertyAnimation, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.models import LauncherItem, LauncherType
from core.windows_shortcuts import (
    is_supported_executable_drop_path,
    supported_target_file_dialog_filter,
)
from ui.card_widget import LauncherItemWidget


class ExeAddSlotCard(QFrame):
    files_selected = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AddSlotCard")
        self.setProperty("dropActive", False)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        plus_label = QLabel("+")
        plus_label.setObjectName("AddSlotPlus")
        plus_label.setAlignment(Qt.AlignCenter)
        plus_label.setFixedSize(44, 44)

        title = QLabel("Add / Drop Target")
        title.setObjectName("AddSlotTitle")

        subtitle = QLabel(
            "Append Windows launch targets like EXE, shortcut, batch, PowerShell, URL, or Arduino sketch."
        )
        subtitle.setObjectName("AddSlotSubtitle")
        subtitle.setWordWrap(True)

        choose_button = QPushButton("Choose Target")
        choose_button.setObjectName("GhostActionButton")
        choose_button.clicked.connect(self._choose_files)

        layout.addWidget(plus_label, 0, Qt.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(choose_button, 0, Qt.AlignLeft)

        for child in self.findChildren(QWidget):
            child.setAcceptDrops(True)
            child.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        event_type = event.type()
        if event_type == QEvent.DragEnter:
            if self._contains_exe(event):
                self._set_drop_active(True)
                event.acceptProposedAction()
                return True
        elif event_type == QEvent.DragMove:
            if self._contains_exe(event):
                self._set_drop_active(True)
                event.acceptProposedAction()
                return True
        elif event_type == QEvent.Drop:
            paths = self._extract_local_paths(event)
            exe_paths = [path for path in paths if is_supported_executable_drop_path(path)]
            self._set_drop_active(False)
            if exe_paths:
                self.files_selected.emit(exe_paths)
                event.acceptProposedAction()
                return True
        elif event_type == QEvent.DragLeave:
            self._set_drop_active(False)

        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event) -> None:
        if self._contains_exe(event):
            self._set_drop_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self._contains_exe(event):
            self._set_drop_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._set_drop_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._set_drop_active(False)
        paths = self._extract_local_paths(event)
        exe_paths = [path for path in paths if is_supported_executable_drop_path(path)]
        if not exe_paths:
            event.ignore()
            return

        self.files_selected.emit(exe_paths)
        event.acceptProposedAction()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self._choose_files()
        super().mouseReleaseEvent(event)

    def _choose_files(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Application Targets",
            str(Path.home()),
            supported_target_file_dialog_filter(),
        )
        if not file_paths:
            return

        self.files_selected.emit([Path(file_path) for file_path in file_paths])

    def _contains_exe(self, event) -> bool:
        return any(is_supported_executable_drop_path(path) for path in self._extract_local_paths(event))

    def _extract_local_paths(self, event) -> list[Path]:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return []

        return [Path(url.toLocalFile()) for url in mime_data.urls() if url.isLocalFile()]

    def _set_drop_active(self, active: bool) -> None:
        self.setProperty("dropActive", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class AnimatedItemStack(QWidget):
    """Animate vertical card reordering with live insertion previews."""

    SPACING = 12
    DURATION_MS = 180

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item_widgets: list[LauncherItemWidget] = []
        self._footer_widget: QWidget | None = None
        self._empty_widget: QWidget | None = None
        self._preview_ids: list[str] = []
        self._dragged_item_id: str | None = None
        self._drag_offset_y = 0
        self._indicator_y: int | None = None
        self._content_height = 0
        self._animation_group: QParallelAnimationGroup | None = None
        self._insert_indicator = QFrame(self)
        self._insert_indicator.setObjectName("InsertIndicator")
        self._insert_indicator.hide()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_widgets(
        self,
        *,
        item_widgets: Sequence[LauncherItemWidget],
        footer_widget: QWidget | None = None,
        empty_widget: QWidget | None = None,
    ) -> None:
        self._clear_children()

        self._item_widgets = list(item_widgets)
        self._footer_widget = footer_widget
        self._empty_widget = empty_widget
        self._preview_ids = []
        self._dragged_item_id = None
        self._drag_offset_y = 0
        self._indicator_y = None
        self._insert_indicator.hide()

        for widget in self._all_widgets():
            widget.setParent(self)
            widget.show()

        self._apply_layout(animate=False)

    def current_item_ids(self) -> list[str]:
        return [widget.item.id for widget in self._item_widgets]

    def preview_reorder(self, dragged_item_id: str, global_pos) -> None:
        current_ids = self.current_item_ids()
        if dragged_item_id not in current_ids:
            return

        preview_ids = self._build_preview_order(dragged_item_id, global_pos)
        if preview_ids == self._preview_ids and self._dragged_item_id == dragged_item_id:
            self._position_dragged_widget(global_pos)
            return

        self._dragged_item_id = dragged_item_id
        self._preview_ids = preview_ids
        self._apply_layout(animate=True)
        self._position_dragged_widget(global_pos)

    def start_drag(self, dragged_item_id: str, global_pos) -> None:
        widget = self._widget_by_id(dragged_item_id)
        if widget is None:
            return

        self._dragged_item_id = dragged_item_id
        self._preview_ids = self.current_item_ids()
        self._drag_offset_y = self.mapFromGlobal(global_pos).y() - widget.geometry().top()
        widget.set_drag_active(True)
        widget.raise_()
        self._apply_layout(animate=True)
        self._position_dragged_widget(global_pos)

    def move_drag(self, dragged_item_id: str, global_pos) -> None:
        if self._dragged_item_id != dragged_item_id:
            return

        self.preview_reorder(dragged_item_id, global_pos)

    def finish_drag(self, dragged_item_id: str, global_pos) -> list[str]:
        if self._dragged_item_id != dragged_item_id:
            return self.current_item_ids()

        self.preview_reorder(dragged_item_id, global_pos)

        widget = self._widget_by_id(dragged_item_id)
        if widget is not None:
            widget.set_drag_active(False)

        ordered_ids = self.preview_order_ids()
        self._dragged_item_id = None
        self._drag_offset_y = 0
        self._apply_layout(animate=True)
        return ordered_ids

    def preview_order_ids(self) -> list[str]:
        return list(self._preview_ids or self.current_item_ids())

    def clear_preview(self, *, animate: bool) -> None:
        if not self._preview_ids and self._dragged_item_id is None:
            return

        for widget in self._item_widgets:
            widget.set_drag_active(False)

        self._preview_ids = []
        self._dragged_item_id = None
        self._drag_offset_y = 0
        self._indicator_y = None
        self._insert_indicator.hide()
        self._apply_layout(animate=animate)

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self._content_height)

    def minimumSizeHint(self) -> QSize:
        return QSize(super().minimumSizeHint().width(), self._content_height)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_layout(animate=False)

    def _build_preview_order(self, dragged_item_id: str, global_pos) -> list[str]:
        ordered_ids = [item_id for item_id in self.current_item_ids() if item_id != dragged_item_id]
        local_y = self.mapFromGlobal(global_pos).y()

        widget_lookup = {widget.item.id: widget for widget in self._item_widgets}
        drop_index = len(ordered_ids)
        for index, item_id in enumerate(ordered_ids):
            widget = widget_lookup[item_id]
            if local_y < widget.geometry().center().y():
                drop_index = index
                break

        ordered_ids.insert(drop_index, dragged_item_id)
        return ordered_ids

    def _apply_layout(self, *, animate: bool) -> None:
        if self.width() <= 0:
            return

        if self._animation_group is not None:
            self._animation_group.stop()
            self._animation_group = None

        widget_lookup = {widget.item.id: widget for widget in self._item_widgets}
        order_ids = self._preview_ids or self.current_item_ids()
        dragged_id = self._dragged_item_id if self._preview_ids else None

        y = 0
        animations: list[QPropertyAnimation] = []
        indicator_y: int | None = None

        for item_id in order_ids:
            widget = widget_lookup[item_id]
            widget_height = self._widget_height(widget)

            if dragged_id == item_id:
                indicator_y = y
                widget.show()
                y += widget_height + self.SPACING
                continue

            widget.set_drag_active(False)
            widget.show()
            target = QRect(0, y, self.width(), widget_height)
            animation = self._set_widget_geometry(widget, target, animate=animate)
            if animation is not None:
                animations.append(animation)
            y += widget_height + self.SPACING

        content_tail = y - self.SPACING if y else 0

        extra_widgets = [widget for widget in (self._empty_widget, self._footer_widget) if widget is not None]
        for widget in extra_widgets:
            widget.show()
            widget_height = self._widget_height(widget)
            target = QRect(0, y, self.width(), widget_height)
            animation = self._set_widget_geometry(widget, target, animate=animate)
            if animation is not None:
                animations.append(animation)
            y += widget_height + self.SPACING
            content_tail = y - self.SPACING

        self._content_height = max(0, content_tail)
        self.setMinimumHeight(self._content_height)
        self.resize(self.width(), self._content_height)
        self._indicator_y = indicator_y
        self._update_insert_indicator()

        if animations:
            group = QParallelAnimationGroup(self)
            for animation in animations:
                group.addAnimation(animation)
            self._animation_group = group
            group.start()

    def _set_widget_geometry(
        self,
        widget: QWidget,
        target: QRect,
        *,
        animate: bool,
    ) -> QPropertyAnimation | None:
        current = widget.geometry()
        if current == target:
            return None

        if not animate:
            widget.setGeometry(target)
            return None

        animation = QPropertyAnimation(widget, b"geometry", self)
        animation.setDuration(self.DURATION_MS)
        animation.setStartValue(current)
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        return animation

    def _widget_height(self, widget: QWidget) -> int:
        hint = widget.sizeHint().height()
        minimum = widget.minimumSizeHint().height()
        return max(hint, minimum, widget.minimumHeight(), 56)

    def _all_widgets(self) -> list[QWidget]:
        widgets = [*self._item_widgets]
        if self._empty_widget is not None:
            widgets.append(self._empty_widget)
        if self._footer_widget is not None:
            widgets.append(self._footer_widget)
        return widgets

    def _clear_children(self) -> None:
        if self._animation_group is not None:
            self._animation_group.stop()
            self._animation_group = None

        for widget in self._all_widgets():
            widget.setParent(None)
            widget.deleteLater()

        self._item_widgets = []
        self._footer_widget = None
        self._empty_widget = None
        self._preview_ids = []
        self._dragged_item_id = None
        self._drag_offset_y = 0
        self._indicator_y = None
        self._content_height = 0
        self._insert_indicator.hide()

    def _update_insert_indicator(self) -> None:
        if self._indicator_y is None or not self._preview_ids:
            self._insert_indicator.hide()
            return

        indicator_x = 34
        indicator_width = max(140, self.width() - 68)
        self._insert_indicator.setGeometry(
            indicator_x,
            max(0, self._indicator_y - 1),
            indicator_width,
            2,
        )
        self._insert_indicator.show()
        self._insert_indicator.raise_()

    def _widget_by_id(self, item_id: str) -> LauncherItemWidget | None:
        for widget in self._item_widgets:
            if widget.item.id == item_id:
                return widget
        return None

    def _position_dragged_widget(self, global_pos) -> None:
        if self._dragged_item_id is None:
            return

        widget = self._widget_by_id(self._dragged_item_id)
        if widget is None:
            return

        local_y = self.mapFromGlobal(global_pos).y() - self._drag_offset_y
        max_top = max(0, self._content_height - widget.height())
        clamped_y = max(0, min(local_y, max_top))
        widget.setGeometry(0, clamped_y, self.width(), widget.height())
        widget.raise_()


class LauncherGroupPanel(QFrame):
    add_requested = Signal(str)
    run_all_requested = Signal(str)
    run_item_requested = Signal(str)
    selection_changed = Signal(str, bool)
    view_script_requested = Signal(str)
    edit_item_requested = Signal(str)
    delete_item_requested = Signal(str)
    item_order_changed = Signal(str, object)
    files_dropped = Signal(object)
    quick_url_submitted = Signal(str)

    def __init__(
        self,
        *,
        group_type: LauncherType,
        title: str,
        subtitle: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.group_type = group_type
        self.setObjectName("GroupPanel")
        self.setAcceptDrops(True)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")

        self.count_badge = QLabel("0 items")
        self.count_badge.setObjectName("MetricPill")
        self.count_badge.setAlignment(Qt.AlignCenter)

        title_row.addWidget(title_label, 1)
        title_row.addWidget(self.count_badge, 0)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("SectionSubtitle")
        subtitle_label.setWordWrap(True)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        run_button = QPushButton("Run URLs" if group_type is LauncherType.URL else "Run EXEs")
        run_button.setObjectName("PrimaryButton")
        run_button.clicked.connect(lambda: self.run_all_requested.emit(self.group_type.value))

        if group_type is LauncherType.URL:
            self.quick_url_input = QLineEdit()
            self.quick_url_input.setObjectName("QuickUrlInput")
            self.quick_url_input.setPlaceholderText("Paste URL and press Enter...")
            self.quick_url_input.returnPressed.connect(self._emit_quick_url)

            add_button = QPushButton("Add")
            add_button.clicked.connect(self._emit_quick_url)

            action_row.addWidget(self.quick_url_input, 1)
            action_row.addWidget(add_button, 0)
            action_row.addWidget(run_button, 0)
        else:
            action_row.addWidget(run_button, 0)
        action_row.addStretch(1)

        header_layout.addLayout(title_row)
        header_layout.addWidget(subtitle_label)
        header_layout.addLayout(action_row)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.items_host = AnimatedItemStack()
        self.scroll_area.setWidget(self.items_host)

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.scroll_area, 1)

        self._register_drop_target_tree(self)
        self._register_drop_target_tree(self.items_host)

    def set_items(self, items: Sequence[LauncherItem], *, selected_ids: set[str] | None = None) -> None:
        self.count_badge.setText(f"{len(items)} items")
        selected_ids = selected_ids or set()

        widgets: list[LauncherItemWidget] = []
        for index, item in enumerate(items, start=1):
            widget = LauncherItemWidget(item, index, selected=item.id in selected_ids)
            widget.run_requested.connect(self.run_item_requested)
            widget.selection_toggled.connect(self.selection_changed)
            widget.view_script_requested.connect(self.view_script_requested)
            widget.edit_requested.connect(self.edit_item_requested)
            widget.delete_requested.connect(self.delete_item_requested)
            widget.reorder_started.connect(self._start_item_reorder)
            widget.reorder_moved.connect(self._move_item_reorder)
            widget.reorder_finished.connect(self._finish_item_reorder)
            widgets.append(widget)

        footer_widget: QWidget | None = None
        empty_widget: QWidget | None = None

        if self.group_type is LauncherType.EXE:
            add_slot = ExeAddSlotCard()
            add_slot.files_selected.connect(self.files_dropped)
            footer_widget = add_slot
        elif not widgets:
            empty_widget = self._build_empty_state()

        self.items_host.set_widgets(
            item_widgets=widgets,
            footer_widget=footer_widget,
            empty_widget=empty_widget,
        )

        self._register_drop_target_tree(self.items_host)
        for widget in widgets:
            self._register_drop_target_tree(widget)
        if footer_widget is not None:
            footer_widget.setAcceptDrops(True)
        if empty_widget is not None:
            self._register_drop_target_tree(empty_widget)

    def reset_reorder_preview(self) -> None:
        self.items_host.clear_preview(animate=True)

    def _start_item_reorder(self, item_id: str, global_pos) -> None:
        self.items_host.start_drag(item_id, global_pos)

    def _move_item_reorder(self, item_id: str, global_pos) -> None:
        self.items_host.move_drag(item_id, global_pos)

    def _finish_item_reorder(self, item_id: str, global_pos) -> None:
        ordered_ids = self.items_host.finish_drag(item_id, global_pos)
        current_ids = self.items_host.current_item_ids()

        if ordered_ids != current_ids:
            self.item_order_changed.emit(self.group_type.value, ordered_ids)
            return

        self.items_host.clear_preview(animate=True)

    def eventFilter(self, watched, event) -> bool:
        event_type = event.type()
        if event_type == QEvent.DragEnter:
            if self._handle_drag_enter(event):
                return True
        elif event_type == QEvent.DragMove:
            if self._handle_drag_move(event):
                return True
        elif event_type == QEvent.Drop:
            if self._handle_drop(event):
                return True

        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event) -> None:
        self._handle_drag_enter(event)

    def dragMoveEvent(self, event) -> None:
        self._handle_drag_move(event)

    def dragLeaveEvent(self, event) -> None:
        self.items_host.clear_preview(animate=True)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._handle_drop(event)

    def _handle_drag_enter(self, event) -> bool:
        if self._contains_internal_item_drag(event):
            dragged_item_id = self._dragged_item_id_from_event(event)
            self.items_host.preview_reorder(dragged_item_id, event.globalPosition().toPoint())
            event.acceptProposedAction()
            return True

        if self._contains_external_exe_drop(event):
            event.acceptProposedAction()
            return True

        event.ignore()
        return False

    def _handle_drag_move(self, event) -> bool:
        if self._contains_internal_item_drag(event):
            dragged_item_id = self._dragged_item_id_from_event(event)
            self.items_host.preview_reorder(dragged_item_id, event.globalPosition().toPoint())
            event.acceptProposedAction()
            return True

        if self._contains_external_exe_drop(event):
            event.acceptProposedAction()
            return True

        event.ignore()
        return False

    def _handle_drop(self, event) -> bool:
        if self._contains_internal_item_drag(event):
            ordered_ids = self.items_host.preview_order_ids()
            current_ids = self.items_host.current_item_ids()
            if ordered_ids != current_ids:
                self.item_order_changed.emit(self.group_type.value, ordered_ids)
            else:
                self.items_host.clear_preview(animate=True)
            event.acceptProposedAction()
            return True

        if self._contains_external_exe_drop(event):
            self.items_host.clear_preview(animate=True)
            self.files_dropped.emit(self._extract_external_drop_paths(event))
            event.acceptProposedAction()
            return True

        event.ignore()
        return False

    def _build_empty_state(self) -> QFrame:
        empty_frame = QFrame()
        empty_frame.setObjectName("EmptyState")

        layout = QVBoxLayout(empty_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        title = QLabel("No URLs yet.")
        title.setObjectName("SectionTitle")

        subtitle = QLabel("Add URLs to build the run order for this group.")
        subtitle.setObjectName("EmptyStateSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return empty_frame

    def _contains_internal_item_drag(self, event) -> bool:
        mime_data = event.mimeData()
        if not mime_data.hasFormat("application/x-orbit-item-id"):
            return False
        if not mime_data.hasFormat("application/x-orbit-group-type"):
            return False

        dragged_group = bytes(mime_data.data("application/x-orbit-group-type")).decode("utf-8")
        return dragged_group == self.group_type.value

    def _dragged_item_id_from_event(self, event) -> str:
        return bytes(event.mimeData().data("application/x-orbit-item-id")).decode("utf-8")

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

    def _register_drop_target_tree(self, widget: QWidget) -> None:
        if not widget.property("_orbitDropFilterInstalled"):
            widget.setAcceptDrops(True)
            widget.installEventFilter(self)
            widget.setProperty("_orbitDropFilterInstalled", True)

        for child in widget.findChildren(QWidget):
            if child.property("_orbitDropFilterInstalled"):
                continue
            child.setAcceptDrops(True)
            child.installEventFilter(self)
            child.setProperty("_orbitDropFilterInstalled", True)

    def _emit_quick_url(self) -> None:
        if self.group_type is not LauncherType.URL:
            return

        text = self.quick_url_input.text().strip()
        if not text:
            return

        self.quick_url_submitted.emit(text)
        self.quick_url_input.clear()
