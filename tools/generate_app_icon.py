from __future__ import annotations

from pathlib import Path
import struct

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QConicalGradient,
    QGradient,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT_DIR / "assets" / "icons"
PNG_NAME = "orbit_panel.png"
ICO_NAME = "orbit_panel.ico"


def _render_icon(size: int) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    rect = QRectF(10, 10, size - 20, size - 20)
    radius = size * 0.23

    background = QLinearGradient(rect.topLeft(), rect.bottomRight())
    background.setColorAt(0.0, QColor("#122235"))
    background.setColorAt(0.52, QColor("#0d1623"))
    background.setColorAt(1.0, QColor("#09111b"))

    outer_path = QPainterPath()
    outer_path.addRoundedRect(rect, radius, radius)
    painter.fillPath(outer_path, background)

    glow = QRadialGradient(rect.center() + QPointF(size * 0.05, -size * 0.1), size * 0.75)
    glow.setColorAt(0.0, QColor(63, 198, 214, 72))
    glow.setColorAt(0.55, QColor(20, 70, 102, 34))
    glow.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.fillPath(outer_path, glow)

    border_pen = QPen(QColor(96, 159, 196, 96), max(2, size // 96))
    painter.setPen(border_pen)
    painter.drawRoundedRect(rect, radius, radius)

    core_rect = QRectF(size * 0.29, size * 0.29, size * 0.42, size * 0.42)
    core_radius = size * 0.085
    core_grad = QLinearGradient(core_rect.topLeft(), core_rect.bottomRight())
    core_grad.setColorAt(0.0, QColor("#f7fbff"))
    core_grad.setColorAt(0.55, QColor("#dff8fa"))
    core_grad.setColorAt(1.0, QColor("#9fdbdf"))
    painter.fillRect(core_rect.adjusted(0, 0, 0, 0), Qt.GlobalColor.transparent)

    core_path = QPainterPath()
    core_path.addRoundedRect(core_rect, core_radius, core_radius)
    painter.fillPath(core_path, core_grad)

    core_outline = QPen(QColor("#6ce0e5"), max(2, size // 110))
    painter.setPen(core_outline)
    painter.drawPath(core_path)

    tile_gap = size * 0.028
    tile_width = (core_rect.width() - tile_gap * 3) / 2
    tile_height = (core_rect.height() - tile_gap * 3) / 2
    tile_color = QColor("#112132")
    accent_tile = QColor("#2dd7df")

    tiles = [
        (core_rect.left() + tile_gap, core_rect.top() + tile_gap, tile_color),
        (core_rect.left() + tile_gap * 2 + tile_width, core_rect.top() + tile_gap, accent_tile),
        (core_rect.left() + tile_gap, core_rect.top() + tile_gap * 2 + tile_height, QColor("#173149")),
        (
            core_rect.left() + tile_gap * 2 + tile_width,
            core_rect.top() + tile_gap * 2 + tile_height,
            QColor("#b9eef2"),
        ),
    ]

    painter.setPen(Qt.PenStyle.NoPen)
    tile_radius = size * 0.03
    for x, y, color in tiles:
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(x, y, tile_width, tile_height), tile_radius, tile_radius)

    ring_rect = rect.adjusted(size * 0.08, size * 0.08, -size * 0.08, -size * 0.08)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    ring_pen = QPen(QColor("#6ce0e5"), max(8, size // 24), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(ring_pen)
    painter.drawArc(ring_rect, 36 * 16, 216 * 16)

    inner_ring_rect = rect.adjusted(size * 0.16, size * 0.2, -size * 0.12, -size * 0.16)
    ring_gradient = QConicalGradient(inner_ring_rect.center(), 148)
    ring_gradient.setCoordinateMode(QGradient.CoordinateMode.ObjectBoundingMode)
    ring_gradient.setColorAt(0.0, QColor("#4ac7ff"))
    ring_gradient.setColorAt(0.38, QColor("#6ce0e5"))
    ring_gradient.setColorAt(0.75, QColor("#2a84c9"))
    ring_gradient.setColorAt(1.0, QColor("#4ac7ff"))

    inner_pen = QPen(ring_gradient, max(6, size // 34), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(inner_pen)
    painter.drawArc(inner_ring_rect, 248 * 16, 112 * 16)

    dot_pen = QPen(Qt.PenStyle.NoPen)
    painter.setPen(dot_pen)
    painter.setBrush(QColor("#6ce0e5"))
    painter.drawEllipse(QRectF(size * 0.71, size * 0.18, size * 0.08, size * 0.08))

    accent_pen = QPen(QColor(255, 255, 255, 38), max(2, size // 128))
    painter.setPen(accent_pen)
    painter.drawArc(rect.adjusted(size * 0.05, size * 0.05, -size * 0.26, -size * 0.28), 120 * 16, 54 * 16)

    painter.end()
    return image


def _to_png_bytes(image: QImage) -> bytes:
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(byte_array)


def _write_ico(output_path: Path, png_payloads: list[tuple[int, bytes]]) -> None:
    count = len(png_payloads)
    header = struct.pack("<HHH", 0, 1, count)
    directory = bytearray()
    offset = 6 + (16 * count)

    for size, payload in png_payloads:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        offset += len(payload)

    with output_path.open("wb") as icon_file:
        icon_file.write(header)
        icon_file.write(directory)
        for _, payload in png_payloads:
            icon_file.write(payload)


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    png_payloads: list[tuple[int, bytes]] = []

    for size in sizes:
        image = _render_icon(size)
        png_payloads.append((size, _to_png_bytes(image)))

    preview_path = ICONS_DIR / PNG_NAME
    preview_image = _render_icon(512)
    preview_image.save(str(preview_path), "PNG")

    ico_path = ICONS_DIR / ICO_NAME
    _write_ico(ico_path, png_payloads)

    print(f"Generated {preview_path}")
    print(f"Generated {ico_path}")


if __name__ == "__main__":
    main()
