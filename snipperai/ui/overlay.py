import os
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from snipperai.ui.theme import get_theme_qss


class SnipperActionMenu(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        
        # Use shared theme for menu controls (greyscale frosted look)
        self.setStyleSheet(get_theme_qss("menu"))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Action Buttons
        self.agent_btn = QPushButton("🤖")
        self.agent_btn.setObjectName("agent_btn")
        self.agent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.agent_btn)

        self.ocr_btn = QPushButton("🔍")
        self.ocr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.ocr_btn)

        self.copy_btn = QPushButton("📋")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.copy_btn)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("settings_btn")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.settings_btn)

        self.close_btn = QPushButton("❌")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.close_btn)


class SnipperOverlay(QWidget):
    action_requested = pyqtSignal(str, str)  # Emits (action_type, image_path)

    def __init__(self, save_path: str = "buffer/snip_buffer.png"):
        super().__init__()
        self.save_path = save_path
        
        screen = QApplication.primaryScreen()
        if not screen:
            raise RuntimeError("Could not detect primary screen.")
        self.full_screenshot = screen.grabWindow(0)
        self.dpr = screen.devicePixelRatio()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        self.current_selection_rect = None
        self.finalized_cropped_image = None

        self.action_menu = SnipperActionMenu(self)
        self.action_menu.hide()
        
        self.action_menu.agent_btn.clicked.connect(lambda: self._trigger_action("EXPLAIN"))
        self.action_menu.ocr_btn.clicked.connect(lambda: self._trigger_action("OCR"))
        self.action_menu.copy_btn.clicked.connect(lambda: self._trigger_action("COPY_IMAGE"))
        self.action_menu.settings_btn.clicked.connect(lambda: self._trigger_action("SETTINGS"))
        self.action_menu.close_btn.clicked.connect(lambda: self._trigger_action("CLOSE"))

    def _trigger_action(self, action_type: str):
        self.hide()
        QApplication.processEvents()

        if action_type not in ("CLOSE", "SETTINGS") and self.finalized_cropped_image:
            output_dir = os.path.dirname(self.save_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            self.finalized_cropped_image.save(self.save_path)

        self.action_requested.emit(action_type, self.save_path)
        self.deleteLater()

    def mousePressEvent(self, event):
        self.action_menu.hide()
        self.begin = event.pos()
        self.end = event.pos()
        self.is_selecting = True
        self.current_selection_rect = None
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False
        
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        width, height = x2 - x1, y2 - y1

        if width > 15 and height > 15:
            self.current_selection_rect = QRect(x1, y1, width, height)
            
            high_res_rect = QRect(
                int(x1 * self.dpr), int(y1 * self.dpr), 
                int(width * self.dpr), int(height * self.dpr)
            )
            self.finalized_cropped_image = self.full_screenshot.copy(high_res_rect)
            
            menu_size = self.action_menu.sizeHint()
            padding = 8

            menu_x = x2 - menu_size.width() - padding
            menu_y = y2 - menu_size.height() - padding

            if menu_x < x1 + padding:
                menu_x = x1 + padding
            if menu_y < y1 + padding:
                menu_y = y1 - menu_size.height() - padding

            screen_rect = self.rect()
            menu_x = max(padding, min(menu_x, screen_rect.width() - menu_size.width() - padding))
            menu_y = max(padding, min(menu_y, screen_rect.height() - menu_size.height() - padding))

            self.action_menu.move(QPoint(int(menu_x), int(menu_y)))
            self.action_menu.show()
            self.update()
        else:
            self.action_menu.hide()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.full_screenshot)
        painter.fillRect(self.rect(), QColor(10, 14, 23, 140))
        
        if self.is_selecting or self.current_selection_rect:
            rect = QRect(self.begin, self.end).normalized() if self.is_selecting else self.current_selection_rect
            painter.drawPixmap(rect, self.full_screenshot, rect)
            painter.setPen(QPen(QColor(71, 71, 71), 1))
            painter.drawRect(rect)