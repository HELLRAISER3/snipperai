from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QColor, QKeySequence, QMouseEvent, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Font stack: real SF Pro on macOS, closest first-party equivalents
# elsewhere. Qt stylesheets resolve font-family like CSS, falling through
# the list to the first family actually installed.
FONT_STACK = (
    '"SF Pro Display", "SF Pro Text", "Segoe UI Variable Text", '
    '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
)


class TrafficLight(QPushButton):
    """A single macOS-style window control dot (close / minimize / zoom)."""

    def __init__(self, fill: str, ring: str, glyph: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setText(glyph)
        self.setFixedSize(12, 12)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {fill};
                border: 0.5px solid {ring};
                border-radius: 6px;
                color: transparent;
                font-size: 9px;
                font-weight: 700;
                padding: 0px;
            }}
            QPushButton:hover {{
                color: rgba(0, 0, 0, 0.55);
            }}
            QPushButton:pressed {{
                background-color: {ring};
            }}
            """
        )


class TitleBar(QFrame):
    """Custom, draggable replacement for the native window chrome."""

    def __init__(self, window: "TextResultWindow"):
        super().__init__(window)
        self._window = window
        self._drag_offset: QPoint | None = None
        self.setObjectName("title_bar")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.close_btn = TrafficLight("#FF5F57", "#E0443E", "\u00d7")
        self.min_btn = TrafficLight("#FEBC2E", "#D89E24", "\u2212")
        self.zoom_btn = TrafficLight("#28C840", "#1DAD34", "+")
        self.close_btn.clicked.connect(window.close)
        self.min_btn.clicked.connect(window.showMinimized)
        self.zoom_btn.clicked.connect(window.toggle_maximized)
        controls.addWidget(self.close_btn)
        controls.addWidget(self.min_btn)
        controls.addWidget(self.zoom_btn)

        # Mirrors the width of the traffic-light cluster so the title
        # label lands dead-center, matching macOS window titlebars.
        spacer = QWidget()
        spacer.setFixedWidth(60)

        self.title_label = QLabel("OCR Result")
        self.title_label.setObjectName("window_title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(controls)
        layout.addWidget(self.title_label, stretch=1)
        layout.addWidget(spacer)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._window.toggle_maximized()


class TextResultWindow(QWidget):
    """macOS-style, frameless OCR result window with a glass-dark panel."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)

        self._configure_window()
        self._build_ui(text)
        self._configure_shortcuts()

        self.reset_timer = QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self._reset_copy_button)

    # ------------------------------------------------------------------ #
    # Window setup
    # ------------------------------------------------------------------ #

    def _configure_window(self) -> None:
        self.setObjectName("root")
        self.setWindowTitle("SnipperAI \u2014 OCR Result")

        # Frameless + translucent so we can paint our own rounded, shadowed
        # panel instead of the OS titlebar/border.
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(720, 520)
        self.setMinimumSize(560, 400)

        self.setStyleSheet(
            f"""
            QWidget#root {{
                background: transparent;
            }}

            QFrame#panel {{
                background-color: #201F22;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }}

            QFrame#title_bar {{
                background-color: rgba(255, 255, 255, 0.02);
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }}

            QLabel#window_title {{
                color: rgba(255, 255, 255, 0.55);
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 600;
            }}

            QLabel#title_label {{
                color: #F5F5F7;
                font-family: {FONT_STACK};
                font-size: 20px;
                font-weight: 700;
                letter-spacing: -0.2px;
            }}

            QLabel#subtitle_label {{
                color: rgba(255, 255, 255, 0.45);
                font-family: {FONT_STACK};
                font-size: 12.5px;
            }}

            QLabel#status_label {{
                background-color: rgba(48, 209, 88, 0.16);
                color: #30D158;
                border: 1px solid rgba(48, 209, 88, 0.35);
                border-radius: 10px;
                padding: 4px 12px;
                font-family: {FONT_STACK};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.3px;
            }}

            QLabel#section_label {{
                color: rgba(255, 255, 255, 0.35);
                font-family: {FONT_STACK};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }}

            QPlainTextEdit#result_editor {{
                background-color: rgba(255, 255, 255, 0.035);
                color: #EDEDED;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 16px;
                selection-background-color: rgba(10, 132, 255, 0.45);
                selection-color: #FFFFFF;
                font-family: {FONT_STACK};
                font-size: 13.5px;
                line-height: 1.6;
            }}

            QPlainTextEdit#result_editor:focus {{
                border: 1px solid #0A84FF;
            }}

            QScrollBar:vertical {{
                background: transparent;
                width: 9px;
                margin: 6px 2px 6px 0;
            }}

            QScrollBar::handle:vertical {{
                background-color: rgba(255, 255, 255, 0.18);
                min-height: 28px;
                border-radius: 4px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: rgba(255, 255, 255, 0.30);
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}

            QPushButton#copy_button {{
                background-color: #0A84FF;
                color: #FFFFFF;
                border: none;
                border-radius: 17px;
                padding: 9px 20px;
                min-width: 130px;
                font-family: {FONT_STACK};
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton#copy_button:hover {{
                background-color: #2E9BFF;
            }}

            QPushButton#copy_button:pressed {{
                background-color: #0060CC;
            }}

            QPushButton#copy_button[state="success"] {{
                background-color: #30D158;
            }}

            QPushButton#copy_button[state="success"]:hover {{
                background-color: #4EDD73;
            }}

            QLabel#footer_label {{
                color: rgba(255, 255, 255, 0.30);
                font-family: {FONT_STACK};
                font-size: 11px;
            }}
            """
        )

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #

    def _build_ui(self, text: str) -> None:
        # Outer layout leaves breathing room around the panel so the drop
        # shadow has somewhere to fall without being clipped by the window.
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(24, 24, 24, 24)

        panel = QFrame()
        panel.setObjectName("panel")
        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(0, 0, 0, 160))
        panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        panel_layout.addWidget(self.title_bar)

        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(28, 22, 28, 20)
        body_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(4)
        title_label = QLabel("OCR Result")
        title_label.setObjectName("title_label")
        subtitle_label = QLabel("Text detected from your last capture")
        subtitle_label.setObjectName("subtitle_label")
        heading_layout.addWidget(title_label)
        heading_layout.addWidget(subtitle_label)

        status_label = QLabel("COMPLETE")
        status_label.setObjectName("status_label")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addLayout(heading_layout)
        header_layout.addStretch()
        header_layout.addWidget(status_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        body_layout.addLayout(header_layout)

        section_label = QLabel("EXTRACTED TEXT")
        section_label.setObjectName("section_label")
        body_layout.addWidget(section_label)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setObjectName("result_editor")
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setPlaceholderText("No text was detected.")
        self.text_edit.setTabChangesFocus(True)
        body_layout.addWidget(self.text_edit, stretch=1)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 2, 0, 0)

        self.footer_label = QLabel()
        self.footer_label.setObjectName("footer_label")
        self._update_text_count()

        self.copy_button = QPushButton("Copy Text")
        self.copy_button.setObjectName("copy_button")
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setAccessibleName("Copy extracted OCR text")
        self.copy_button.clicked.connect(self.copy_to_clipboard)

        footer_layout.addWidget(self.footer_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.copy_button)

        body_layout.addLayout(footer_layout)
        panel_layout.addLayout(body_layout)

        outer_layout.addWidget(panel)

    def _configure_shortcuts(self) -> None:
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.copy_shortcut.activated.connect(self.copy_to_clipboard)
        self.text_edit.textChanged.connect(self._update_text_count)

    # ------------------------------------------------------------------ #
    # Behaviour
    # ------------------------------------------------------------------ #

    def toggle_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _update_text_count(self) -> None:
        text = self.text_edit.toPlainText()
        character_count = len(text)
        word_count = len(text.split())
        self.footer_label.setText(f"{word_count:,} words  \u00b7  {character_count:,} characters")

    def copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return

        text = self.text_edit.toPlainText()
        if not text.strip():
            return

        clipboard.setText(text)

        self.copy_button.setText("Copied")
        self.copy_button.setProperty("state", "success")
        self._refresh_widget_style(self.copy_button)

        self.reset_timer.start(1800)

    def _reset_copy_button(self) -> None:
        self.copy_button.setText("Copy Text")
        self.copy_button.setProperty("state", "")
        self._refresh_widget_style(self.copy_button)

    @staticmethod
    def _refresh_widget_style(widget: QWidget) -> None:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)