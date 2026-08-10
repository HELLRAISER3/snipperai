import os
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap

class SnipperOverlay(QWidget):
    snippet_captured = pyqtSignal(str)

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

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.is_selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False
        
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        width, height = x2 - x1, y2 - y1

        if width > 5 and height > 5:
            crop_rect = QRect(
                int(x1 * self.dpr), 
                int(y1 * self.dpr), 
                int(width * self.dpr), 
                int(height * self.dpr)
            )
            cropped_image = self.full_screenshot.copy(crop_rect)
            
            output_dir = os.path.dirname(self.save_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            cropped_image.save(self.save_path)
            print(f"Captured clean area: {width}x{height} saved to {self.save_path}")
            
            self.snippet_captured.emit(self.save_path)

        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw base frozen desktop
        painter.drawPixmap(0, 0, self.full_screenshot)
        
        # Apply dark mask layer over everything
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))
        
        if self.is_selecting:
            rect = QRect(self.begin, self.end).normalized()
            
            # Un-tint selected rectangular region
            painter.drawPixmap(rect, self.full_screenshot, rect)
            
            # Selection border
            painter.setPen(QPen(QColor(120, 120, 120), 2))
            painter.drawRect(rect)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Quick standalone test execution
    def on_captured(path):
        print(f"Signal received! File ready at: {path}")

    snipper = SnipperOverlay()
    snipper.snippet_captured.connect(on_captured)
    snipper.show()
    sys.exit(app.exec())