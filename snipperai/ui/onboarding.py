from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from snipperai.cloud.agent import is_valid_api_key
from snipperai.config import settings
from snipperai.ui.controls import (
    DotIndicator,
    HoverButton,
    HoverFrame,
    LabeledField,
    TitleBar,
    ToggleSwitch,
)
from snipperai.ui.theme import get_theme_qss


def _page(title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
    """Builds a page shell with the standard heading block, and returns
    the page plus its content layout so callers can add page-specific
    fields below the heading."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)

    title_label = QLabel(title)
    title_label.setObjectName("onboarding_title")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("onboarding_subtitle")
    subtitle_label.setWordWrap(True)

    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    return page, layout


class OnboardingWizard(QDialog):
    """Three-step first-run setup: welcome, API key, preferences."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("SnipperAI Setup")
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(560, 520)
        self.setMinimumSize(520, 480)
        self.setStyleSheet(get_theme_qss("onboarding"))

        self._build_pages()
        self._build_ui()
        self._refresh_nav()

    # Pages

    def _build_pages(self) -> None:
        self.stack = QStackedWidget()

        # Page 1: Welcome
        welcome, welcome_layout = _page(
            "Welcome to SnipperAI",
            "Your AI-powered desktop snippet and OCR assistant.",
        )
        body = QLabel(
            "Capture any area on your screen, run instant OCR, or ask an AI "
            "model questions about what's on screen.\n\n"
            "Let's get you configured in two quick steps."
        )
        body.setObjectName("onboarding_body")
        body.setWordWrap(True)
        welcome_layout.addWidget(body)
        welcome_layout.addStretch()
        self.stack.addWidget(welcome)

        # Page 2: API key
        api_page, api_layout = _page(
            "OpenRouter API Key",
            "Provide your key to enable multi-modal AI reasoning.",
        )
        key_field = LabeledField("API Key")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-or-v1-...")
        self.api_key_input.textChanged.connect(self._refresh_nav)
        key_field.row.addWidget(self.api_key_input, stretch=1)
        api_layout.addWidget(key_field)

        self.key_warning = QLabel("This doesn't look like a valid API key.")
        self.key_warning.setObjectName("warning_label")
        self.key_warning.setWordWrap(True)
        self.key_warning.hide()
        api_layout.addWidget(self.key_warning)

        api_layout.addStretch()
        self.stack.addWidget(api_page)

        # Page 3: Preferences
        prefs_page, prefs_layout = _page(
            "App Preferences",
            "Configure how you launch SnipperAI.",
        )
        hotkey_field = LabeledField("Global Hotkey")
        self.hotkey_input = QLineEdit("ctrl+shift+s")
        hotkey_field.row.addWidget(self.hotkey_input, stretch=1)
        prefs_layout.addWidget(hotkey_field)

        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 4, 0, 0)
        toggle_label = QLabel("Launch SnipperAI on system startup")
        toggle_label.setObjectName("toggle_label")
        self.autostart_toggle = ToggleSwitch(checked=False)
        toggle_row.addWidget(toggle_label)
        toggle_row.addStretch()
        toggle_row.addWidget(self.autostart_toggle)
        toggle_container = QWidget()
        toggle_container.setLayout(toggle_row)
        prefs_layout.addWidget(toggle_container)
        prefs_layout.addStretch()
        self.stack.addWidget(prefs_page)

    # Chrome

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)

        panel = HoverFrame()
        panel.setObjectName("panel")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        panel_layout.addWidget(
            TitleBar(self, "Setup", show_minimize=False, show_maximize=False)
        )

        body = QVBoxLayout()
        body.setContentsMargins(28, 24, 28, 22)
        body.setSpacing(20)
        body.addWidget(self.stack, stretch=1)

        self.dots = DotIndicator(self.stack.count())
        body.addWidget(self.dots)

        nav_row = QHBoxLayout()
        self.back_btn = HoverButton("Back")
        self.back_btn.setObjectName("ghost_button")
        self.back_btn.clicked.connect(self._go_back)

        self.next_btn = HoverButton("Next")
        self.next_btn.setObjectName("primary_button")
        self.next_btn.clicked.connect(self._go_next)

        nav_row.addWidget(self.back_btn)
        nav_row.addStretch()
        nav_row.addWidget(self.next_btn)
        body.addLayout(nav_row)

        panel_layout.addLayout(body)
        outer.addWidget(panel)

    # Navigation

    def _refresh_nav(self) -> None:
        index = self.stack.currentIndex()
        is_last = index == self.stack.count() - 1

        self.back_btn.setEnabled(index > 0)
        self.next_btn.setText("Finish" if is_last else "Next")
        self.dots.set_active(index)

        if index == 1:
            key = self.api_key_input.text()
            valid = is_valid_api_key(key)
            self.key_warning.setVisible(bool(key) and not valid)
            self.next_btn.setEnabled(valid)
        else:
            self.next_btn.setEnabled(True)

    def _go_back(self) -> None:
        self.stack.setCurrentIndex(self.stack.currentIndex() - 1)
        self._refresh_nav()

    def _go_next(self) -> None:
        if self.stack.currentIndex() == self.stack.count() - 1:
            self.accept()
            return
        self.stack.setCurrentIndex(self.stack.currentIndex() + 1)
        self._refresh_nav()

    # Completion

    def accept(self) -> None:
        """Save settings once onboarding completes successfully."""
        api_key = self.api_key_input.text().strip()
        hotkey = self.hotkey_input.text().strip() or "ctrl+shift+s"
        autostart = self.autostart_toggle.isChecked()

        settings.save_settings(
            api_key=api_key,
            hotkey=hotkey,
            autostart=autostart,
            first_launch=False,
        )
        super().accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)