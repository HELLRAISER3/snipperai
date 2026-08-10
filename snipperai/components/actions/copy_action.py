from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap

class CopyAction:
    @staticmethod
    def execute(image_path: str) -> bool:
        """Copies the image at image_path to system clipboard."""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setPixmap(pixmap)
                return True
        return False