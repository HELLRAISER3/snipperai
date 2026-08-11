# snipperai/ui/onboarding.py

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QFormLayout
)
from PyQt6.QtCore import Qt
from snipperai.config import settings


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to SnipperAI 🚀")
        self.setSubTitle("Your AI-powered desktop snippet and OCR assistant.")

        layout = QVBoxLayout(self)
        lbl = QLabel(
            "SnipperAI allows you to capture any area on your screen, "
            "perform instant OCR, or ask questions to AI language models.\n\n"
            "Let's get you configured in just two quick steps!"
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)


class ApiKeyPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Step 1: OpenRouter API Key")
        self.setSubTitle("Provide your key to enable multi-modal AI reasoning.")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-or-v1-...")

        # Register mandatory field (Next button won't enable until filled)
        self.registerField("api_key*", self.api_key_input)

        form.addRow(QLabel("API Key:"), self.api_key_input)
        layout.addLayout(form)


class PreferencesPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Step 2: App Preferences")
        self.setSubTitle("Configure how you launch SnipperAI.")

        layout = QVBoxLayout(self)

        self.hotkey_input = QLineEdit("ctrl+shift+s")
        self.registerField("hotkey", self.hotkey_input)

        form = QFormLayout()
        form.addRow(QLabel("Global Hotkey:"), self.hotkey_input)
        layout.addLayout(form)

        self.autostart_checkbox = QCheckBox("Launch SnipperAI on system startup")
        self.registerField("autostart", self.autostart_checkbox)
        layout.addWidget(self.autostart_checkbox)


class OnboardingWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SnipperAI Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)

        self.addPage(WelcomePage())
        self.addPage(ApiKeyPage())
        self.addPage(PreferencesPage())

    def accept(self):
        """Save settings once onboarding completes successfully."""
        api_key = self.field("api_key").strip()
        hotkey = self.field("hotkey").strip() or "ctrl+shift+s"
        autostart = self.field("autostart")

        settings.save_settings(
            api_key=api_key,
            hotkey=hotkey,
            autostart=autostart,
            first_launch=False,
        )
        super().accept()