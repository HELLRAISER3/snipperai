from typing import Optional
from PyQt6.QtWidgets import QWidget
from snipperai.ui.settings_dialog import SettingsDialog


class SettingsAction:
    def __init__(self, parent_widget: Optional[QWidget] = None):
        self.parent_widget = parent_widget

    def execute(self, image_path: Optional[str] = None, **kwargs) -> bool:
        dialog = SettingsDialog(parent=self.parent_widget)
        result = dialog.show() # .exec() for modal window
        return result == SettingsDialog.DialogCode.Accepted