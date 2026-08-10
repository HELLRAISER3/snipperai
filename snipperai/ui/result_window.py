from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QApplication
from PyQt6.QtCore import Qt

class TextResultWindow(QWidget):
    def __init__(self, text: str):
        super().__init__()
        self.setWindowTitle("SnipperAI - Extracted Text")
        self.resize(500, 300)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        layout.addWidget(self.text_edit)

        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_btn)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        self.copy_btn.setText("Copied!")