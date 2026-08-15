from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

SIZES = [16, 24, 32, 48, 64, 128, 256]


def _rasterize_svg(src: Path, render_size: int = 512) -> Image.Image:
    from PyQt6.QtCore import QByteArray, Qt
    from PyQt6.QtGui import QGuiApplication, QImage, QPainter
    from PyQt6.QtSvg import QSvgRenderer

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)

    renderer = QSvgRenderer(QByteArray(src.read_bytes()))
    if not renderer.isValid():
        raise ValueError(f"Qt couldn't parse this SVG: {src}")

    image = QImage(render_size, render_size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    buf = QByteArray()
    from PyQt6.QtCore import QBuffer, QIODevice
    qbuffer = QBuffer(buf)
    qbuffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(qbuffer, "PNG")
    qbuffer.close()

    import io
    return Image.open(io.BytesIO(bytes(buf))).convert("RGBA")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run python snipperai/utils/make_icon.py path/to/logo.png")
        raise SystemExit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"Not found: {src}")
        raise SystemExit(1)

    out = Path(__file__).resolve().parent.parent.parent / "packaging" / "icon.ico"
    out.parent.mkdir(parents=True, exist_ok=True)

    if src.suffix.lower() == ".svg":
        img = _rasterize_svg(src)
    else:
        img = Image.open(src).convert("RGBA")

    img.save(out, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()