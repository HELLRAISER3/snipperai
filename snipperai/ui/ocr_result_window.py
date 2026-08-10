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
                background-color: #0F172A; /* Slate 900 */
                color: #F8FAFC;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QLabel#header_label {
                font-size: 14px;
                font-weight: 600;
                color: #94A3B8;
            }
            QTextEdit {
                background-color: #1E293B; /* Slate 800 */
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: 'Consolas', 'Cascadia Code', monospace;
                selection-background-color: #2563EB;
            }
            QTextEdit:focus {
                border: 1px solid #3B82F6;
            }
            /* Custom Scrollbar */
            QScrollBar:vertical {
                background: #1E293B;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748B;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QPushButton#copy_btn {
                background-color: #2563EB; /* Accent Blue */
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#copy_btn:hover {
                background-color: #3B82F6;
            }
            QPushButton#copy_btn:pressed {
                background-color: #1D4ED8;
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