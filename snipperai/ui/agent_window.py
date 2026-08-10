import importlib
import os
import re
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from langchain_core.messages import HumanMessage, AIMessage

from snipperai.components.actions import AgentAction


class InferenceWorker(QThread):
    """Runs the AI inference in a background thread to prevent UI freezing."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        action: AgentAction,
        prompt: str,
        image_path: Optional[str] = None,
        chat_history: Optional[list] = None,
    ):
        super().__init__()
        self.action = action
        self.prompt = prompt
        self.image_path = image_path
        self.chat_history = chat_history or []

    def run(self):
        try:
            response = self.action.execute(
                image_path=self.image_path,
                prompt=self.prompt,
                chat_history=self.chat_history,
            )
            self.finished.emit(response)
        except Exception as exc:
            self.error.emit(f"AI Inference Error: {exc}")


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
        self.image_label.setStyleSheet(
            "border: 1px solid #334155; border-radius: 4px; background-color: #1E293B;"
        )
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            self.image_label.setPixmap(
                pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
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

    def _escape_html(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _simple_markdown_to_html(self, text: str) -> str:
        escaped = self._escape_html(text)

        escaped = re.sub(
            r"```(?:[^\n]*\n)?(.*?)```",
            r"<pre><code>\1</code></pre>",
            escaped,
            flags=re.S,
        )
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"__(.+?)__", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
        escaped = re.sub(r"_(.+?)_", r"<em>\1</em>", escaped)
        escaped = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            r"<a href=\"\2\">\1</a>",
            escaped,
        )

        lines = escaped.splitlines()
        html_lines = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append("")
                continue

            list_match = re.match(r"^[-*+]\s+(.*)$", stripped)
            if list_match:
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{list_match.group(1)}</li>")
                continue

            if in_list:
                html_lines.append("</ul>")
                in_list = False

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                html_lines.append(
                    f"<h{level}>{heading_match.group(2)}</h{level}>"
                )
                continue

            html_lines.append(stripped.replace("\n", "<br>"))

        if in_list:
            html_lines.append("</ul>")

        return "<br>".join(html_lines)

    def _render_markdown(self, text: str) -> str:
        try:
            markdown = importlib.import_module("markdown")

            return markdown.markdown(
                text,
                extensions=["fenced_code", "codehilite", "nl2br"],
            )
        except (ImportError, ModuleNotFoundError):
            return self._simple_markdown_to_html(text)

    def append_message(self, role: str, text: str):
        """Formats and appends a message to the chat display."""
        color = "#60A5FA" if role == "User" else "#34D399"
        if role == "Error":
            color = "#F87171"

        body = (
            self._render_markdown(text)
            if role == "SnipperAI"
            else self._escape_html(text).replace("\n", "<br>")
        )

        html = (
            f'<div style="margin-bottom:12px;">'
            f'<b style="color:{color};">{role}:</b><br>{body}</div>'
        )
        self.chat_display.append(html)

    def _start_initial_analysis(self):
        """Triggers the first inference automatically."""
        self.append_message("System", "Analyzing snippet...")
        self._run_inference(
            "Explain what is shown in this snippet concisely. Provide clear and actionable insights.",
            include_image=True,
        )

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

        self.worker = InferenceWorker(
            self.agent_action,
            prompt,
            image_to_send,
            self.chat_history,
        )
        self.worker.finished.connect(
            lambda res: self._on_inference_success(res, prompt, include_image)
        )
        self.worker.error.connect(self._on_inference_error)
        self.worker.start()

    def _on_inference_success(
        self,
        response_text: str,
        original_prompt: str,
        included_image: bool,
    ):
        """Handles successful AI response and updates LangChain history."""
        if included_image and self.agent_action._agent is not None:
            msg = self.agent_action._agent.build_multimodal_message(
                original_prompt,
                self.image_path,
            )
            self.chat_history.append(msg)
        else:
            self.chat_history.append(HumanMessage(content=original_prompt))

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