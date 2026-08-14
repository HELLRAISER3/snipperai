# snipperai/ui/ocr_result_window.py
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
from snipperai.ui.controls import HoverButton, HoverFrame, TitleBar
from snipperai.ui.theme import get_theme_qss


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

        self.resize(750, 560)
        self.setMinimumSize(590, 430)

        self.setStyleSheet(get_theme_qss("ocr"))

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #

    def _build_ui(self, text: str) -> None:
        # Outer layout leaves breathing room around the panel so the drop
        # shadow has somewhere to fall without being clipped by the window.
        # This margin (40px) must stay ahead of HoverFrame's shadow reach
        # (blurRadius + y-offset, see controls.py) or Windows' layered-
        # window compositor can be handed an out-of-bounds dirty rect.
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(40, 40, 40, 40)

        panel = HoverFrame()
        panel.setObjectName("panel")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self.title_bar = TitleBar(self, "OCR Result")
        panel_layout.addWidget(self.title_bar)

        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(28, 22, 28, 20)
        body_layout.setSpacing(16)

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(4)
        title_label = QLabel("OCR Result")
        title_label.setObjectName("title_label")
        subtitle_label = QLabel("Text detected from your last capture")
        subtitle_label.setObjectName("subtitle_label")
        heading_layout.addWidget(title_label)
        heading_layout.addWidget(subtitle_label)

        body_layout.addLayout(heading_layout)

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

        self.copy_button = HoverButton("Copy Text")
        self.copy_button.setObjectName("copy_button")
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

        # Deferred to the next event-loop tick rather than restyled
        # synchronously inside the click handler. On Windows, a frameless
        # WA_TranslucentBackground window paired with a QGraphicsEffect
        # can crash with "UpdateLayeredWindowIndirect failed" if a style
        # repolish + repaint happens inside the same paint cycle as the
        # click that triggered it. QTimer.singleShot(0, ...) pushes the
        # restyle to a clean frame instead.
        QTimer.singleShot(0, lambda: self._refresh_widget_style(self.copy_button))

        self.reset_timer.start(1800)

    def _reset_copy_button(self) -> None:
        self.copy_button.setText("Copy Text")
        self.copy_button.setProperty("state", "")
        QTimer.singleShot(0, lambda: self._refresh_widget_style(self.copy_button))

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