from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

class TextResultWindow(QWidget):
    def __init__(self, text: str):
        super().__init__()
        self.setWindowTitle("SnipperAI - Scanned Result")
        self.resize(520, 340)
        self.setMinimumSize(400, 250)
        
        # Always stay on top of other windows
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # Base Dark Theme & Glassmorphism Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #F3F4F6;
                color: #111827;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QLabel#header_label {
                font-size: 14px;
                font-weight: 700;
                color: #111827;
            }
            QTextEdit {
                background-color: #FFFFFF;
                color: #111827;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 14px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                selection-background-color: #BFDBFE;
            }
            QTextEdit:focus {
                border: 1px solid #93C5FD;
            }
            QScrollBar:vertical {
                background: #F3F4F6;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QPushButton#copy_btn {
                background-color: #E0E7FF;
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#copy_btn:hover {
                background-color: #DBEAFE;
            }
            QPushButton#copy_btn:pressed {
                background-color: #BFDBFE;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header bar
        header_layout = QHBoxLayout()
        header = QLabel("⚡ Scanned Text")
        header.setObjectName("header_label")
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Text editor / display box
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        layout.addWidget(self.text_edit)

        # Bottom action bar
        self.copy_btn = QPushButton("📋 Copy to Clipboard")
        self.copy_btn.setObjectName("copy_btn")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_btn)

        # Timer to reset copy button label back to default after 2 seconds
        self.reset_timer = QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self._reset_button_text)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.text_edit.toPlainText())
            self.copy_btn.setText("✓ Copied!")
            self.copy_btn.setStyleSheet("""
                QPushButton#copy_btn {
                    background-color: #059669; /* Success Green */
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 16px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
            self.reset_timer.start(2000)

    def _reset_button_text(self):
        self.copy_btn.setText("📋 Copy to Clipboard")
        self.copy_btn.setStyleSheet("")  