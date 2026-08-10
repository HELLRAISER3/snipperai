import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from langchain_core.messages import HumanMessage, AIMessage

from snipperai.components.actions import AgentAction

class InferenceWorker(QThread):
    """Runs the AI inference in a background thread to prevent UI freezing."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, action: AgentAction, prompt: str, image_path: str = None, chat_history: list = None):
        super().__init__()
        self.action = action
        self.prompt = prompt
        self.image_path = image_path
        self.chat_history = chat_history or []

    def run(self):
        try:
            # Ensure the agent is instantiated safely
            if self.action._agent is None:
                from snipperai.agent import SnipperAgent
                self.action._agent = SnipperAgent()
            
            response = self.action._agent.invoke(
                prompt=self.prompt, 
                image_path=self.image_path,
                chat_history=self.chat_history
            )
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(f"AI Inference Error: {str(e)}")


class AgentChatWindow(QWidget):
    """A dedicated, polished chat interface for communicating with SnipperAI."""
    def __init__(self, image_path: str, agent_action: AgentAction):
        super().__init__()
        self.image_path = image_path
        self.agent_action = agent_action
        self.chat_history = []
        
        self.setWindowTitle("SnipperAI - Agent Conversation")
        self.resize(600, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #0F172A;
                color: #F8FAFC;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94A3B8;
            }
        """)

        self._setup_ui()
        self._start_initial_analysis()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header: Image Preview
        header_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setFixedSize(120, 80)
        self.image_label.setStyleSheet("border: 1px solid #334155; border-radius: 4px; background-color: #1E293B;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.image_label.setText("No Image")

        info_label = QLabel("Chatting with SnipperAI about this capture.")
        info_label.setStyleSheet("color: #94A3B8; font-size: 13px;")
        
        header_layout.addWidget(self.image_label)
        header_layout.addWidget(info_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Chat Display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Input Area
        input_layout = QHBoxLayout### 1. Diagnosing the "User not found" Error

The error shown in `image_604fa3.png` (`AI Inference Error: User not found.`) is a standard HTTP 401 response from the OpenRouter API. This happens when your application successfully connects to OpenRouter, but the API key provided cannot be matched to an active user account.

Here is why this typically occurs:
*   **Invalid or Expired Key:** The API key has been revoked, deleted, or has expired.
*   **Incorrect Key Format:** OpenRouter keys strictly start with `sk-or-`. If you accidentally pasted an OpenAI key (which starts with `sk-...`) or a model ID, authentication will fail.
*   **Configuration Loading Issue:** The environment variable or configuration file is not being read correctly by SnipperAI, resulting in an empty or malformed token being sent.

**The Fix:**
Navigate to `https://openrouter.ai/keys`, generate a brand-new API key (ensuring it begins with `sk-or-v1-`), and paste it securely into SnipperAI's settings or configuration file. 

---

### 2. Building the Interactive Agent Chat Window

To create a "pretty and intelligent" conversation window for SnipperAI, we must ensure the main GUI does not freeze while waiting for the AI model to reply. We will achieve this by isolating the inference call inside a background `QThread`.

Create a new file for this UI component.

**`snipperai/ui/agent_window.py`**
```python
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from langchain_core.messages import HumanMessage, AIMessage

from snipperai.components.actions import AgentAction

class InferenceWorker(QThread):
    """Runs the AI inference in a background thread to prevent UI freezing."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, action: AgentAction, prompt: str, image_path: str = None, chat_history: list = None):
        super().__init__()
        self.action = action
        self.prompt = prompt
        self.image_path = image_path
        self.chat_history = chat_history or []

    def run(self):
        try:
            # Ensure the agent is instantiated safely
            if self.action._agent is None:
                from snipperai.agent import SnipperAgent
                self.action._agent = SnipperAgent()
            
            response = self.action._agent.invoke(
                prompt=self.prompt, 
                image_path=self.image_path,
                chat_history=self.chat_history
            )
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(f"AI Inference Error: {str(e)}")


class AgentChatWindow(QWidget):
    """A dedicated, polished chat interface for communicating with SnipperAI."""
    def __init__(self, image_path: str, agent_action: AgentAction):
        super().__init__()
        self.image_path = image_path
        self.agent_action = agent_action
        self.chat_history = []
        
        self.setWindowTitle("SnipperAI - Agent Conversation")
        self.resize(600, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #0F172A;
                color: #F8FAFC;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94A3B8;
            }
        """)

        self._setup_ui()
        self._start_initial_analysis()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header: Image Preview
        header_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setFixedSize(120, 80)
        self.image_label.setStyleSheet("border: 1px solid #334155; border-radius: 4px; background-color: #1E293B;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.image_label.setText("No Image")

        info_label = QLabel("Chatting with SnipperAI about this capture.")
        info_label.setStyleSheet("color: #94A3B8; font-size: 13px;")
        
        header_layout.addWidget(self.image_label)
        header_layout.addWidget(info_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Chat Display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a follow-up question...")
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

    def append_message(self, role: str, text: str):
        """Formats and appends a message to the chat display."""
        color = "#60A5FA" if role == "User" else "#34D399"
        if role == "Error":
            color = "#F87171"
            
        html = f'<div style="margin-bottom:12px;"><b style="color:{color};">{role}:</b><br>{text}</div>'
        self.chat_display.append(html)

    def _start_initial_analysis(self):
        """Triggers the first inference automatically."""
        self.append_message("System", "Analyzing snippet...")
        self._run_inference("Explain what is shown in this snippet concisely. Provide clear and actionable insights.", include_image=True)

    def send_message(self):
        """Handles user input and triggers subsequent inferences."""
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        self.input_field.clear()
        self.append_message("User", user_text)
        self._run_inference(user_text, include_image=False)

    def _run_inference(self, prompt: str, include_image: bool = False):
        """Disables UI, sets up the worker thread, and starts inference."""
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)

        image_to_send = self.image_path if include_image else None
        
        self.worker = InferenceWorker(self.agent_action, prompt, image_to_send, self.chat_history)
        self.worker.finished.connect(lambda res: self._on_inference_success(res, prompt, include_image))
        self.worker.error.connect(self._on_inference_error)
        self.worker.start()

    def _on_inference_success(self, response_text: str, original_prompt: str, included_image: bool):
        """Handles successful AI response and updates LangChain history."""
        # Update history with the user's prompt (multimodal or text-only)
        if included_image and self.agent_action._agent is not None:
             msg = self.agent_action._agent.build_multimodal_message(original_prompt, self.image_path)
             self.chat_history.append(msg)
        else:
             self.chat_history.append(HumanMessage(content=original_prompt))
             
        # Append the AI's response to history and UI
        self.chat_history.append(AIMessage(content=response_text))
        self.append_message("SnipperAI", response_text)
        self._cleanup_worker()

    def _on_inference_error(self, error_msg: str):
        """Displays errors gracefully in the chat."""
        self.append_message("Error", error_msg)
        self._cleanup_worker()

    def _cleanup_worker(self):
        """Re-enables the UI after the thread finishes."""
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()