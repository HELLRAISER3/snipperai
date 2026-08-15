# snipperai/ui/controls.py
"""Shared, custom-painted widgets for SnipperAI's glass UI.

Every top-level window should be built from these primitives instead of
raw Qt widgets + inline stylesheets:

- `HoverFrame`   the floating glass panel every window sits in (bakes in
                  the elevation shadow, so no window has to remember one)
- `TitleBar`     frameless, draggable, macOS-style traffic-light chrome
- `HoverButton`  base QPushButton with the right cursor; styling comes
                  from theme.py by object name (#primary_button /
                  #ghost_button / default)
- `ToggleSwitch` hand-painted boolean switch - never use QCheckBox,
                  its native indicator can't be reskinned to match
- `SectionCard`  replaces QGroupBox, which also can't be fully reskinned
                  (its title notch is native chrome)
- `LabeledField` a small label-over-row layout helper for form rows
- `DotIndicator` page-progress dots, for onboarding-style flows

Native controls (QCheckBox, QGroupBox, QWizard's button box, the OS
titlebar) only take partial styling from Qt stylesheets - real visual
consistency requires custom-painted or custom-composed replacements,
which is what this module provides.
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QMouseEvent, QPainter
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from snipperai.ui.theme import CANVAS, TEXT_PRIMARY


# --------------------------------------------------------------------------- #
# Panel
# --------------------------------------------------------------------------- #


class HoverFrame(QFrame):
    """The floating glass panel every window is built on.

    Owns the elevation shadow so it's applied exactly once, consistently,
    rather than every window re-adding a QGraphicsDropShadowEffect with
    slightly different numbers.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # blurRadius + y-offset must stay comfortably inside whatever
        # margin the window reserves around the panel (see each window's
        # outer_layout margins). If the shadow's effective reach exceeds
        # that margin, its bounding rect can extend past the top-level
        # window's own buffer - on Windows this produces malformed dirty
        # rects and crashes with "UpdateLayeredWindowIndirect failed:
        # The parameter is incorrect" the next time anything in the
        # window triggers a style repolish. Keep reach (blur + offset)
        # a few px under the smallest margin any window uses (40px).
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)


# --------------------------------------------------------------------------- #
# Title bar / window chrome
# --------------------------------------------------------------------------- #


class TrafficDot(QPushButton):
    """A single monochrome window-control dot (close / minimize / zoom).

    Since color can't signal which control does what (strict black/white/
    grey palette), the glyph stays faintly visible at rest rather than
    only appearing on hover.
    """

    def __init__(self, glyph: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setText(glyph)
        self.setFixedSize(13, 13)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.10);
                border: 0.5px solid rgba(255, 255, 255, 0.14);
                border-radius: 6.5px;
                color: rgba(255, 255, 255, 0.45);
                font-size: 9px;
                font-weight: 700;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.18);
                color: rgba(255, 255, 255, 0.85);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.26);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.15);
            }
            """
        )


class TitleBar(QFrame):
    """Frameless, draggable replacement for the native window titlebar.

    A dot is shown-but-disabled (rather than hidden) when its action isn't
    available, so the title stays perfectly centered regardless of which
    controls a given window offers.
    """

    def __init__(
        self,
        window: QWidget,
        title: str,
        show_minimize: bool = True,
        show_maximize: bool = True,
    ):
        super().__init__(window)
        self._window = window
        self._drag_offset: QPoint | None = None
        self._can_maximize = show_maximize and hasattr(window, "toggle_maximized")

        self.setObjectName("title_bar")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.min_btn = TrafficDot("\u2212")
        if show_minimize and hasattr(window, "showMinimized"):
            self.min_btn.clicked.connect(window.showMinimized)
        else:
            self.min_btn.setEnabled(False)
        controls.addWidget(self.min_btn)

        self.zoom_btn = TrafficDot("+")
        if self._can_maximize:
            self.zoom_btn.clicked.connect(window.toggle_maximized)
        else:
            self.zoom_btn.setEnabled(False)
        controls.addWidget(self.zoom_btn)

        self.close_btn = TrafficDot("\u00d7")
        self.close_btn.clicked.connect(window.close)
        controls.addWidget(self.close_btn)

        # Mirrors the control cluster's width so the title lands
        # dead-center, matching Windows titlebar layout (controls right).
        spacer = QWidget()
        spacer.setFixedWidth(61)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("window_title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(spacer)
        layout.addWidget(self.title_label, stretch=1)
        layout.addLayout(controls)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self._can_maximize:
            self._window.toggle_maximized()


# --------------------------------------------------------------------------- #
# Buttons
# --------------------------------------------------------------------------- #


class HoverButton(QPushButton):
    """QPushButton with the right cursor. Visuals come entirely from
    theme.py by object name - this exists as a distinct class mainly so
    the app's own buttons are easy to reason about separately from any
    buttons Qt draws internally."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


# --------------------------------------------------------------------------- #
# Toggle switch (replaces QCheckBox everywhere)
# --------------------------------------------------------------------------- #


class ToggleSwitch(QWidget):
    """A hand-painted, monochrome toggle switch.

    QCheckBox's native indicator can't be fully reskinned across
    platforms - this paints itself directly instead, and animates the
    knob so it reads as "liquid" rather than a flat state flip.
    """

    def __init__(self, parent: QWidget | None = None, checked: bool = False):
        super().__init__(parent)
        self.setFixedSize(42, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._knob_x = 21.0 if checked else 3.0

        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool) -> None:
        if value == self._checked:
            return
        self._checked = value
        self._anim.stop()
        self._anim.setStartValue(self._knob_x)
        self._anim.setEndValue(21.0 if value else 3.0)
        self._anim.start()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def _get_knob_pos(self) -> float:
        return self._knob_x

    def _set_knob_pos(self, value: float) -> None:
        self._knob_x = value
        self.update()

    knobPos = pyqtProperty(float, _get_knob_pos, _set_knob_pos)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = QColor(TEXT_PRIMARY) if self._checked else QColor(255, 255, 255, 30)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)

        knob_color = QColor(CANVAS) if self._checked else QColor(210, 210, 210)
        painter.setBrush(knob_color)
        painter.drawEllipse(int(self._knob_x), 3, 18, 18)


# --------------------------------------------------------------------------- #
# Section card (replaces QGroupBox everywhere)
# --------------------------------------------------------------------------- #


class SectionCard(QFrame):
    """A single elevation step above the panel background.

    Use instead of QGroupBox - a QGroupBox's title notch is drawn by the
    native style engine and never fully matches a custom theme.
    """

    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 18)
        self._layout.setSpacing(14)

        heading = QLabel(title.upper())
        heading.setObjectName("card_title")
        self._layout.addWidget(heading)

    def add_row(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)


class LabeledField(QWidget):
    """A label stacked above a horizontal row - the standard form-row
    shape used across settings/onboarding (label + input [+ button])."""

    def __init__(self, label: str, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label_widget = QLabel(label)
        label_widget.setObjectName("field_label")
        layout.addWidget(label_widget)

        self.row = QHBoxLayout()
        self.row.setSpacing(8)
        layout.addLayout(self.row)


# --------------------------------------------------------------------------- #
# Page-progress dots (onboarding-style flows)
# --------------------------------------------------------------------------- #


class DotIndicator(QWidget):
    """Small centered row of progress dots, e.g. for a multi-step wizard."""

    def __init__(self, count: int, parent: QWidget | None = None):
        super().__init__(parent)
        self._dots: list[QLabel] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addStretch()
        for _ in range(count):
            dot = QLabel("\u2022")
            dot.setObjectName("dot_inactive")
            self._dots.append(dot)
            layout.addWidget(dot)
        layout.addStretch()

        if self._dots:
            self.set_active(0)

    def set_active(self, index: int) -> None:
        for i, dot in enumerate(self._dots):
            dot.setObjectName("dot_active" if i == index else "dot_inactive")
            dot.style().unpolish(dot)
            dot.style().polish(dot)