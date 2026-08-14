# snipperai/ui/agent_chat_window.py
import importlib
import os
import re
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from langchain_core.messages import HumanMessage, AIMessage

from snipperai.cloud.agent import AgentError, InvalidApiKeyError, MissingApiKeyError
from snipperai.components.actions import AgentAction
from snipperai.ui.controls import HoverButton, HoverFrame, TitleBar
from snipperai.ui.theme import TEXT_PRIMARY, TEXT_TERTIARY, get_theme_qss


class InferenceWorker(QThread):
    """Runs the AI inference in a background thread to prevent UI freezing."""

    finished = pyqtSignal(str)
    error = pyqtSignal(object)  # emits an AgentError, not a string

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
            result = self.action.execute(
                image_path=self.image_path,
                prompt=self.prompt,
                chat_history=self.chat_history,
            )
        except Exception:
            # Safety net: AgentAction.execute() shouldn't raise (it returns
            # a result object either way), but if it somehow does, still
            # never leak the raw exception into the chat window.
            self.error.emit(
                AgentError("Something unexpected happened. Please try again.", retryable=True)
            )
            return

        if result.ok:
            self.finished.emit(result.text)
        else:
            self.error.emit(result.error)


class AgentChatWindow(QWidget):
    """Frameless, glass-panel chat interface for talking to SnipperAI."""

    # Emitted when the user hits an API-key-related error and should be
    # sent to Settings to fix it. Connect this to your Settings dialog's
    # open logic from wherever AgentChatWindow is constructed, e.g.:
    #   window.open_settings_requested.connect(lambda: SettingsDialog(window).exec())
    open_settings_requested = pyqtSignal()

    def __init__(self, image_path: str, agent_action: AgentAction):
        super().__init__()
        self.image_path = image_path
        self.agent_action = agent_action
        self.chat_history = []

        self._configure_window()
        self._setup_ui()
        self._start_initial_analysis()

    # ------------------------------------------------------------------ #
    # Window setup
    # ------------------------------------------------------------------ #

    def _configure_window(self) -> None:
        self.setObjectName("root")
        self.setWindowTitle("SnipperAI \u2014 Agent Conversation")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(660, 760)
        self.setMinimumSize(520, 520)
        self.setStyleSheet(get_theme_qss("agent"))

    def toggle_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)

        panel = HoverFrame()
        panel.setObjectName("panel")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        panel_layout.addWidget(TitleBar(self, "Agent Conversation"))

        body = QVBoxLayout()
        body.setContentsMargins(24, 20, 24, 20)
        body.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.image_label = QLabel()
        self.image_label.setObjectName("thumb_frame")
        self.image_label.setFixedSize(112, 76)
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
        info_label.setObjectName("agent_info_label")
        info_label.setWordWrap(True)

        header_layout.addWidget(self.image_label)
        header_layout.addWidget(info_label, stretch=1)
        body.addLayout(header_layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        body.addWidget(self.chat_display, stretch=1)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a follow-up question...")
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = HoverButton("Send")
        self.send_btn.setObjectName("send_button")
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field, stretch=1)
        input_layout.addWidget(self.send_btn)
        body.addLayout(input_layout)

        panel_layout.addLayout(body)
        outer.addWidget(panel)

    # ------------------------------------------------------------------ #
    # Markdown / LaTeX rendering (unchanged logic, kept as-is)
    # ------------------------------------------------------------------ #

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
            s = s.replace(r"\infty", "\u221e")
            s = s.replace(r"\sum", "\u2211")
            s = s.replace(r"\int", "\u222b")
            s = s.replace(r"\sin", "sin")
            s = s.replace(r"\cos", "cos")
            s = s.replace(r"\ln", "ln")
            s = s.replace(r"\in", "\u2208")
            s = s.replace(r"\times", "\u00d7")
            s = s.replace(r"\leq", "\u2264")
            s = s.replace(r"\geq", "\u2265")
            s = s.replace(r"\neq", "\u2260")

            s = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", s)

            s = s.replace("\\", "")
            return f"<code>{s}</code>"

        text = re.sub(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$", clean_match, text, flags=re.DOTALL)
        text = re.sub(r"\\\((.*?)\\\)|\$([^\$]+)\$", clean_match, text, flags=re.DOTALL)

        return text

    # Placeholder wrappers used to protect code spans while the regexes
    # below run. These MUST contain no Markdown-significant characters
    # (_, *, `, #, -) - the previous version used "___CODEBLOCK_N___" /
    # "___INLINECODE_N___", and the leading/trailing triple underscores
    # were themselves matched by this method's own emphasis regexes
    # (`_(.+?)_` / `__(.+?)__`), tearing the placeholder apart into
    # "<strong><em>INLINECODE_N</em></strong>"-style garbage before the
    # substitution-back step ever ran. Plain alphanumeric tokens can't
    # collide with any of the regexes below.
    _CODEBLOCK_TOKEN = "SNIPPERAICODEBLOCKPLACEHOLDER"
    _INLINECODE_TOKEN = "SNIPPERAIINLINECODEPLACEHOLDER"

    def _simple_markdown_to_html(self, text: str) -> str:
        code_blocks = []

        def stash_block(m):
            code_blocks.append(f"<pre><code>{self._escape_html(m.group(1))}</code></pre>")
            return f"{self._CODEBLOCK_TOKEN}{len(code_blocks)-1}{self._CODEBLOCK_TOKEN}"

        text = re.sub(r"```(?:[^\n]*\n)?(.*?)```", stash_block, text, flags=re.S)

        inline_codes = []

        def stash_inline(m):
            inline_codes.append(f"<code>{self._escape_html(m.group(1))}</code>")
            return f"{self._INLINECODE_TOKEN}{len(inline_codes)-1}{self._INLINECODE_TOKEN}"

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
            result = result.replace(f"{self._INLINECODE_TOKEN}{i}{self._INLINECODE_TOKEN}", code)
        for i, code in enumerate(code_blocks):
            result = result.replace(f"{self._CODEBLOCK_TOKEN}{i}{self._CODEBLOCK_TOKEN}", code)

        return result

    def _render_markdown(self, text: str) -> str:
        text = self._latex_to_unicode(text)
        try:
            markdown = importlib.import_module("markdown")
            html = markdown.markdown(text, extensions=["fenced_code", "codehilite"])
            html = re.sub(r"<h([1-6])>", r'<h\1 style="margin-top:6px; margin-bottom:2px; padding:0; line-height:1.2;">', html)
            html = re.sub(r"<p>", r'<p style="margin-top:2px; margin-bottom:4px; line-height:1.35;">', html)
            html = re.sub(r"<ul>", r'<ul style="margin-top:2px; margin-bottom:4px; padding-left:20px;">', html)
            html = re.sub(r"<li>", r'<li style="margin-bottom:2px;">', html)
            return html
        except (ImportError, ModuleNotFoundError):
            return self._simple_markdown_to_html(text)

    # ------------------------------------------------------------------ #
    # Chat rendering - monochrome, hierarchy via alignment/weight not color
    # ------------------------------------------------------------------ #

    @staticmethod
    def _truncate(text: str, limit: int = 400) -> str:
        text = text.strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "\u2026"

    def append_message(self, role: str, text: str) -> None:
        """Formats and appends a message to the chat display.

        Role is signaled without color (strict monochrome): user messages
        are right-aligned, SnipperAI's are left-aligned, and System/Error
        notices render as small centered italic captions - the same trick
        chat UIs use color for, done here with layout and weight instead.

        System/Error text is truncated defensively: those messages should
        always be short, curated strings from AgentError.user_message, but
        capping length here means a future bug upstream can't dump a huge
        blob (raw exception text, a stray traceback, etc.) into the chat
        again the way the old `f"AI Inference Error: {exc}"` path did.
        """
        if role in ("System", "Error"):
            html = (
                f'<p style="text-align:center; color:{TEXT_TERTIARY}; '
                f'font-size:11px; font-style:italic; margin:10px 0;">'
                f"{self._escape_html(self._truncate(text))}</p>"
            )
            self.chat_display.append(html)
            return

        align = "right" if role == "User" else "left"
        body = (
            self._render_markdown(text)
            if role == "SnipperAI"
            else f'<p style="margin:2px 0;">{self._escape_html(text)}</p>'
        )

        html = f"""
        <div style="text-align:{align}; margin-bottom:16px;">
            <span style="color:{TEXT_TERTIARY}; font-size:10.5px; font-weight:700;
                         letter-spacing:0.5px;">{role.upper()}</span>
            <div style="margin-top:4px; color:{TEXT_PRIMARY}; text-align:left;
                        display:inline-block;">{body}</div>
        </div>
        """
        self.chat_display.append(html)

    # ------------------------------------------------------------------ #
    # Inference plumbing (unchanged)
    # ------------------------------------------------------------------ #

    def _start_initial_analysis(self):
        self.append_message("System", "Analyzing snippet...")
        self._run_inference(
            "Explain what is shown in this snippet concisely. Provide clear and actionable insights.",
            include_image=True,
        )

    def send_message(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        self.input_field.clear()
        self.append_message("User", user_text)
        self._run_inference(user_text, include_image=False)

    def _run_inference(self, prompt: str, include_image: bool = False):
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)

        image_to_send = self.image_path if include_image else None

        self.worker = InferenceWorker(self.agent_action, prompt, image_to_send, self.chat_history)
        self.worker.finished.connect(
            lambda res: self._on_inference_success(res, prompt, include_image)
        )
        self.worker.error.connect(self._on_inference_error)
        self.worker.start()

    def _on_inference_success(self, response_text: str, original_prompt: str, included_image: bool):
        if included_image and self.agent_action._agent is not None:
            msg = self.agent_action._agent.build_multimodal_message(original_prompt, self.image_path)
            self.chat_history.append(msg)
        else:
            self.chat_history.append(HumanMessage(content=original_prompt))

        self.chat_history.append(AIMessage(content=response_text))
        self.append_message("SnipperAI", response_text)
        self._cleanup_worker()

    def _on_inference_error(self, error: AgentError) -> None:
        """Renders a classified, user-safe error - never raw exception
        text, and never through the markdown/code-block rendering path
        (that combination is what produced the "ghost code" artifact:
        an unbounded raw exception string landing in a `<pre><code>`
        block with no explicit color, inheriting a near-invisible
        default). Errors always go through the Error role instead.
        """
        self.append_message("Error", error.user_message)

        if isinstance(error, (MissingApiKeyError, InvalidApiKeyError)):
            self.append_message(
                "System",
                "Open Settings to add or update your OpenRouter API key, then try again.",
            )
            self.open_settings_requested.emit()

        self._cleanup_worker()

    def _cleanup_worker(self):
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)