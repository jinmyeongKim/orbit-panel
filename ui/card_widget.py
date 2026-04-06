from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileIconProvider,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.models import LauncherItem, LauncherType


class DragHandleLabel(QLabel):
    drag_started = Signal(str, object)
    drag_moved = Signal(str, object)
    drag_finished = Signal(str, object)

    def __init__(self, item_id: str, group_type: LauncherType, parent: QWidget | None = None) -> None:
        super().__init__("::", parent)
        self._item_id = item_id
        self._group_type = group_type
        self._drag_start_position = QPoint()
        self._dragging = False

        self.setObjectName("DragHandle")
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.OpenHandCursor)
        self.setFixedWidth(26)
        self.setFixedHeight(42)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.position().toPoint()
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.LeftButton):
            return

        current_pos = event.position().toPoint()
        if not self._dragging:
            if (current_pos - self._drag_start_position).manhattanLength() < QApplication.startDragDistance():
                return
            self._dragging = True
            self.grabMouse()
            self.drag_started.emit(self._item_id, self.mapToGlobal(current_pos))

        self.drag_moved.emit(self._item_id, self.mapToGlobal(current_pos))

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging:
            self.releaseMouse()
            self.drag_finished.emit(self._item_id, self.mapToGlobal(event.position().toPoint()))
            self._dragging = False
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)


class ElidedLabel(QLabel):
    def __init__(self, elide_mode: Qt.TextElideMode, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = ""
        self._elide_mode = elide_mode
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(72)

    def set_full_text(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        super().setText(text)
        self.updateGeometry()
        self._apply_elide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_elide()

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        return QSize(max(72, hint.width()), hint.height())

    def _apply_elide(self) -> None:
        available_width = self.contentsRect().width()
        if available_width <= 0:
            return

        self.setText(self.fontMetrics().elidedText(self._full_text, self._elide_mode, available_width))


class LauncherItemWidget(QFrame):
    run_requested = Signal(str)
    selection_toggled = Signal(str, bool)
    view_script_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    reorder_started = Signal(str, object)
    reorder_moved = Signal(str, object)
    reorder_finished = Signal(str, object)

    def __init__(
        self,
        item: LauncherItem,
        order_index: int,
        *,
        selected: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self.order_index = order_index
        self._initial_selected = selected

        self.setObjectName("ItemFrame")
        self.setProperty("disabledItem", not item.enabled)
        self.setProperty("dragActive", False)
        self.setProperty("selectedItem", selected)
        self.setProperty("hovered", False)
        self.setProperty("pressed", False)
        self.setFrameShape(QFrame.NoFrame)
        self.setMouseTracking(True)
        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)

        self._build_ui()
        self._apply_state()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(18)

        info_row = QHBoxLayout()
        info_row.setContentsMargins(0, 0, 0, 0)
        info_row.setSpacing(16)

        drag_handle = DragHandleLabel(self.item.id, self.item.type)
        drag_handle.drag_started.connect(self.reorder_started)
        drag_handle.drag_moved.connect(self.reorder_moved)
        drag_handle.drag_finished.connect(self.reorder_finished)

        order_badge = QLabel(str(self.order_index))
        order_badge.setObjectName("OrderBadge")
        order_badge.setAlignment(Qt.AlignCenter)
        order_badge.setFixedSize(42, 42)

        app_icon = QLabel()
        app_icon.setObjectName("ItemAppIcon")
        app_icon.setAlignment(Qt.AlignCenter)
        app_icon.setFixedSize(48, 48)
        self._apply_app_icon(app_icon)

        text_block = QWidget()
        text_block.setObjectName("ItemTextBlock")
        text_layout = QHBoxLayout(text_block)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(12)

        title_label = ElidedLabel(Qt.ElideRight)
        title_label.setObjectName("ItemTitle")
        title_label.set_full_text(self._title_text())
        title_label.setMinimumWidth(116)

        secondary_widget = self._build_secondary_info()

        text_layout.addWidget(title_label, 1)
        if secondary_widget is not None:
            text_layout.addWidget(secondary_widget, 0)

        info_row.addWidget(drag_handle, 0, Qt.AlignVCenter)
        info_row.addWidget(order_badge, 0, Qt.AlignVCenter)
        info_row.addWidget(app_icon, 0, Qt.AlignVCenter)
        info_row.addWidget(text_block, 1, Qt.AlignVCenter)

        text_block.setToolTip(self.item.target)
        self.setToolTip(self.item.target)

        info_host = QWidget()
        info_host.setObjectName("ItemInfoHost")
        info_host.setLayout(info_row)

        run_button = QPushButton("Run")
        run_button.setObjectName("ItemPrimaryAction")
        run_button.clicked.connect(lambda: self.run_requested.emit(self.item.id))

        self.select_button = QPushButton("Select")
        self.select_button.setObjectName("ItemSelectAction")
        self.select_button.setCheckable(True)
        self.select_button.setChecked(self._initial_selected)
        self.select_button.toggled.connect(self._handle_selection_toggled)

        script_button = QPushButton("Script")
        script_button.setObjectName("ItemSecondaryAction")
        script_button.clicked.connect(lambda: self.view_script_requested.emit(self.item.id))

        edit_button = QPushButton("Edit")
        edit_button.setObjectName("ItemSecondaryAction")
        edit_button.clicked.connect(lambda: self.edit_requested.emit(self.item.id))

        delete_button = QPushButton("Delete")
        delete_button.setObjectName("ItemDangerAction")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.item.id))

        actions_host = QWidget()
        actions_host.setObjectName("ButtonStrip")
        actions_layout = QHBoxLayout(actions_host)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)
        actions_layout.addWidget(run_button)
        actions_layout.addWidget(self.select_button)

        self.secondary_actions_host = QWidget()
        self.secondary_actions_host.setObjectName("SecondaryActionRow")
        secondary_actions_layout = QHBoxLayout(self.secondary_actions_host)
        secondary_actions_layout.setContentsMargins(0, 0, 0, 0)
        secondary_actions_layout.setSpacing(8)
        secondary_actions_layout.addWidget(script_button)
        secondary_actions_layout.addWidget(edit_button)
        secondary_actions_layout.addWidget(delete_button)

        actions_layout.addWidget(self.secondary_actions_host)

        root_layout.addWidget(info_host, 1)
        root_layout.addWidget(actions_host, 0, Qt.AlignVCenter)

    def _build_secondary_info(self) -> QWidget | None:
        return None

    def _title_text(self) -> str:
        if self.item.title.strip():
            return self.item.title.strip()

        if self.item.type is LauncherType.EXE:
            target_path = Path(os.path.expandvars(self.item.target)).expanduser()
            return target_path.stem or target_path.name or self.item.target

        return self.item.target

    def _apply_app_icon(self, label: QLabel) -> None:
        if self.item.type is LauncherType.URL:
            label.setPixmap(QPixmap())
            label.setText("URL")
            return

        pixmap = self._main_icon_pixmap(28)
        if pixmap is not None:
            label.setPixmap(pixmap)
            label.setText("")
            return

        label.setPixmap(QPixmap())
        label.setText("URL" if self.item.type is LauncherType.URL else "APP")

    def _main_icon_pixmap(self, size: int) -> QPixmap | None:
        icon_source = self._icon_source_path()
        if icon_source is None or not icon_source.exists():
            return None

        provider = QFileIconProvider()
        icon = provider.icon(QFileInfo(str(icon_source)))
        pixmap = icon.pixmap(size, size)
        if pixmap.isNull():
            return None
        return pixmap

    def _icon_source_path(self) -> Path | None:
        candidate = self.item.icon or self.item.target
        if not candidate:
            return None

        path = Path(os.path.expandvars(candidate)).expanduser()
        try:
            return path.resolve(strict=False)
        except OSError:
            return path

    def _apply_state(self) -> None:
        self._update_opacity()
        self._refresh_style()

    def enterEvent(self, event) -> None:
        self.setProperty("hovered", True)
        self._refresh_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.setProperty("hovered", False)
        self.setProperty("pressed", False)
        self._refresh_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.setProperty("pressed", True)
            self._refresh_style()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.setProperty("pressed", False)
        self._refresh_style()
        super().mouseReleaseEvent(event)

    def _refresh_style(self) -> None:
        self.setProperty("selectedItem", self.select_button.isChecked() if hasattr(self, "select_button") else False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _handle_selection_toggled(self, checked: bool) -> None:
        self.select_button.setText("Selected" if checked else "Select")
        self.selection_toggled.emit(self.item.id, checked)
        self._refresh_style()

    def set_drag_active(self, active: bool) -> None:
        if bool(self.property("dragActive")) == active:
            return

        self.setProperty("dragActive", active)
        self._update_opacity()
        self._refresh_style()

    def _update_opacity(self) -> None:
        opacity = 1.0 if self.item.enabled else 0.55
        if self.property("dragActive"):
            opacity *= 0.82
        self._opacity_effect.setOpacity(opacity)
