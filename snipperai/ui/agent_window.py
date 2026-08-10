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
                background-color: #F3F4F6;
                color: #111827;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit {
                background-color: #FFFFFF;
                color: #111827;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                padding: 14px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #93C5FD;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #111827;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                min-height: 38px;
            }
            QLineEdit:focus {
                border: 1px solid #93C5FD;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #111827;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #EFF6FF;
                border-color: #BFDBFE;
            }
            QPushButton:disabled {
                background-color: #F8FAFC;
                color: #9CA3AF;
                border-color: #E5E7EB;
            }
        """)

        self._setup_ui()
        self._start_initial_analysis()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

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

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

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

    def _latex_to_unicode(self, text: str) -> str:
        """Converts common LaTeX math syntax into clean Unicode text for native rendering."""
        def clean_match(m):
            tex = m.group(1) or m.group(2) or ""
            if not tex:
                return ""
            
            s = tex.strip()
            s = s.replace(r"\infty", "∞")
            s = s.replace(r"\sum", "∑")
            s = s.replace(r"\int", "∫")
            s = s.replace(r"\sin", "sin")
            s = s.replace(r"\cos", "cos")
            s = s.replace(r"\ln", "ln")
            s = s.replace(r"\in", "∈")
            s = s.replace(r"\times", "×")
            s = s.replace(r"\leq", "≤")
            s = s.replace(r"\geq", "≥")
            s = s.replace(r"\neq", "≠")
            
            s = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", s)
            
            s = s.replace("\\", "")
            return f"<code>{s}</code>"

        text = re.sub(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$", clean_match, text, flags=re.DOTALL)
        text = re.sub(r"\\\((.*?)\\\)|\$([^\$]+)\$", clean_match, text, flags=re.DOTALL)

        return text

    def _simple_markdown_to_html(self, text: str) -> str:
        code_blocks = []
        def stash_block(m):
            code_blocks.append(f"<pre><code>{self._escape_html(m.group(1))}</code></pre>")
            return f"___CODEBLOCK_{len(code_blocks)-1}___"
        
        text = re.sub(r"```(?:[^\n]*\n)?(.*?)```", stash_block, text, flags=re.S)

        inline_codes = []
        def stash_inline(m):
            inline_codes.append(f"<code>{self._escape_html(m.group(1))}</code>")
            return f"___INLINECODE_{len(inline_codes)-1}___"

        text = re.sub(r"`([^`]+)`", stash_inline, text)

        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)

        lines = text.splitlines()
        html_lines = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                continue

            list_match = re.match(r"^[-*+]\s+(.*)$", stripped)
            if list_match:
                if not in_list:
                    html_lines.append('<ul style="margin-top:2px; margin-bottom:4px; padding-left:20px;">')
                    in_list = True
                html_lines.append(f'<li style="margin-bottom:2px;">{list_match.group(1)}</li>')
                continue

            if in_list:
                html_lines.append("</ul>")
                in_list = False

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                html_lines.append(
                    f'<h{level} style="margin-top:6px; margin-bottom:2px; padding:0; line-height:1.2;">{heading_match.group(2)}</h{level}>'
                )
                continue

            html_lines.append(f'<p style="margin-top:2px; margin-bottom:4px; line-height:1.35;">{stripped}</p>')

        if in_list:
            html_lines.append("</ul>")

        result = "".join(html_lines)

        for i, code in enumerate(inline_codes):
            result = result.replace(f"___INLINECODE_{i}___", code)
        for i, code in enumerate(code_blocks):
            result = result.replace(f"___CODEBLOCK_{i}___", code)

        return result

    def _render_markdown(self, text: str) -> str:
        text = self._latex_to_unicode(text)
        try:
            markdown = importlib.import_module("markdown")
            html = markdown.markdown(
                text,
                extensions=["fenced_code", "codehilite"],
            )
            html = re.sub(r"<h([1-6])>", r'<h\1 style="margin-top:6px; margin-bottom:2px; padding:0; line-height:1.2;">', html)
            html = re.sub(r"<p>", r'<p style="margin-top:2px; margin-bottom:4px; line-height:1.35;">', html)
            html = re.sub(r"<ul>", r'<ul style="margin-top:2px; margin-bottom:4px; padding-left:20px;">', html)
            html = re.sub(r"<li>", r'<li style="margin-bottom:2px;">', html)
            return html
        except (ImportError, ModuleNotFoundError):
            return self._simple_markdown_to_html(text)

    def append_message(self, role: str, text: str):
        """Formats and appends a message to the chat display."""
        color = "#2563EB" if role == "User" else "#059669"
        if role == "Error":
            color = "#DC2626"

        body = (
            self._render_markdown(text)
            if role == "SnipperAI"
            else f'<p style="margin-top:2px; margin-bottom:4px; line-height:1.35;">{self._escape_html(text)}</p>'
        )

        html = f"""
        <div style="margin-bottom:8px;">
            <b style="color:{color}; font-size:14px;">{role}:</b>
            <div style="margin-top:2px;">{body}</div>
        </div>
        """
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