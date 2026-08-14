"""Loads the app's custom SVG action icons."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon

_ICONS_DIR = Path(__file__).resolve().parent / "icons"


def icon(name: str) -> QIcon:
    """Loads `<name>.svg` from the icons directory as a QIcon."""
    path = _ICONS_DIR / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(f"Missing icon: {path}")
    return QIcon(str(path))