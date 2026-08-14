from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from snipperai.cloud.agent import is_valid_api_key
from snipperai.config import settings
from snipperai.ui.controls import (
    HoverButton,
    HoverFrame,
    LabeledField,
    SectionCard,
    TitleBar,
    ToggleSwitch,
)
from snipperai.ui.theme import get_theme_qss


class SettingsDialog(QDialog):
    """Frameless, glass-panel settings dialog bound to app config."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("SnipperAI \u2014 Settings")
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(500, 560)
        self.setMinimumSize(460, 520)

        self.setStyleSheet(get_theme_qss("settings"))

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)

        panel = HoverFrame()
        panel.setObjectName("panel")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        # Modal dialog: no minimize/maximize, close only.
        panel_layout.addWidget(
            TitleBar(self, "Settings", show_minimize=False, show_maximize=False)
        )

        body = QVBoxLayout()
        body.setContentsMargins(24, 22, 24, 22)
        body.setSpacing(16)

        # API Authentication card
        auth_card = SectionCard("API Authentication (BYOK)")
        key_field = LabeledField("OpenRouter Key")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-or-v1-...")
        self.api_key_input.textChanged.connect(self._validate_api_key)
        self.toggle_key_btn = HoverButton("Show")
        self.toggle_key_btn.setObjectName("ghost_button")
        self.toggle_key_btn.setFixedWidth(70)
        self.toggle_key_btn.clicked.connect(self._toggle_key_visibility)
        key_field.row.addWidget(self.api_key_input, stretch=1)
        key_field.row.addWidget(self.toggle_key_btn)
        auth_card.add_row(key_field)

        self.key_warning = QLabel("This doesn't look like a valid API key.")
        self.key_warning.setObjectName("warning_label")
        self.key_warning.setWordWrap(True)
        self.key_warning.hide()
        auth_card.add_row(self.key_warning)

        body.addWidget(auth_card)

        # Preferences card
        prefs_card = SectionCard("Preferences")

        hotkey_field = LabeledField("Global Hotkey")
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("e.g. Ctrl+Shift+S")
        hotkey_field.row.addWidget(self.hotkey_input, stretch=1)
        prefs_card.add_row(hotkey_field)

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
        prefs_card.add_row(toggle_container)

        body.addWidget(prefs_card)
        body.addStretch()

        # Footer actions
        footer = QHBoxLayout()
        footer.addStretch()
        cancel_btn = HoverButton("Cancel")
        cancel_btn.setObjectName("ghost_button")
        cancel_btn.clicked.connect(self.reject)
        save_btn = HoverButton("Save Settings")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(self._save_settings)
        footer.addWidget(cancel_btn)
        footer.addWidget(save_btn)
        body.addLayout(footer)

        panel_layout.addLayout(body)
        outer.addWidget(panel)

    def _toggle_key_visibility(self) -> None:
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("Show")

    def _validate_api_key(self) -> None:
        text = self.api_key_input.text()
        self.key_warning.setVisible(bool(text) and not is_valid_api_key(text))

    def _load_settings(self) -> None:
        """Populates UI controls with values loaded from `config.py`."""
        if settings.openrouter_api_key:
            self.api_key_input.setText(settings.openrouter_api_key)

        self.hotkey_input.setText(getattr(settings, "hotkey", "Ctrl+Shift+S"))
        self.autostart_toggle.setChecked(getattr(settings, "autostart", False))
        self._validate_api_key()

    def _save_settings(self) -> None:
        """Persists settings to disk via `Settings.save_settings()`."""
        api_key = self.api_key_input.text().strip() or None
        hotkey = self.hotkey_input.text().strip() or "Ctrl+Shift+S"
        autostart = self.autostart_toggle.isChecked()

        if api_key is not None and not is_valid_api_key(api_key):
            QMessageBox.warning(
                self,
                "Invalid API Key",
                "This doesn't look like a valid OpenRouter API key. "
                "Double-check what you pasted \u2014 it may be the wrong text.",
            )
            return

        try:
            settings.save_settings(api_key=api_key, hotkey=hotkey, autostart=autostart)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Error Saving Config", f"Could not write configuration to disk: {e}"
            )

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)