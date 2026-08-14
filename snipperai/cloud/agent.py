# snipperai/cloud/agent.py
import base64
import logging
from typing import List, Optional, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter

from snipperai.config import settings

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Typed, user-safe errors
#
# Every one of these carries a short `user_message` that's already safe and
# useful to show directly in the UI - no exception internals, no tracebacks,
# no request/response dumps. The raw underlying exception is still logged
# (via `logger.exception`) so it's recoverable for debugging, it just never
# reaches the chat window.
#
# `MissingApiKeyError` also inherits from ValueError so any existing code
# that catches ValueError for "no key configured" keeps working unchanged.
# --------------------------------------------------------------------------- #


class AgentError(Exception):
    """Base class for agent failures with a message that's safe to show
    directly to the user, plus whether retrying is likely to help."""

    def __init__(self, user_message: str, *, retryable: bool = False):
        super().__init__(user_message)
        self.user_message = user_message
        self.retryable = retryable


class MissingApiKeyError(AgentError, ValueError):
    """No API key configured at all."""


class InvalidApiKeyError(AgentError):
    """Key was provided but rejected by OpenRouter (expired/revoked/typo)."""


class RateLimitedError(AgentError):
    """Too many requests."""


class ConnectionFailedError(AgentError):
    """Couldn't reach OpenRouter at all (network/DNS/timeout)."""


class SnipperAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "openai/gpt-4o-mini",
        temperature: float = 0.7,
    ):
        """
        Initializes the agent. Accepts a user-provided API key,
        falling back to local Settings if not explicitly provided.
        """
        resolved_key = api_key or getattr(settings, "openrouter_api_key", None)

        if not resolved_key or not resolved_key.strip():
            raise MissingApiKeyError(
                "No OpenRouter API key is configured yet. Add one in "
                "Settings to start chatting with SnipperAI."
            )

        self.llm = ChatOpenRouter(
            api_key=resolved_key,
            model=model_name,
            temperature=temperature,
        )

        self.system_prompt = (
            "You are SnipperAI, a desktop assistant. Analyze the user's snippet/screenshot "
            "and query concisely. Give clear, direct, actionable answers."
        )

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Converts a local image file to a base64 string."""
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

    def build_multimodal_message(self, text_query: str, image_path: Optional[str] = None) -> HumanMessage:
        """
        Formats user text and optional screenshot image into a LangChain HumanMessage.
        """
        if not image_path:
            return HumanMessage(content=text_query)

        base64_image = self._encode_image_to_base64(image_path)

        content = [
            {"type": "text", "text": text_query},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            },
        ]
        return HumanMessage(content=content)

    def _classify_error(self, exc: Exception) -> AgentError:
        """Turns an arbitrary exception from the LLM call into a typed,
        user-safe AgentError. Classification is heuristic (status code if
        present, otherwise message text) since the exact exception types
        raised depend on the installed langchain/OpenRouter client version.
        """
        logger.exception("SnipperAgent inference call failed")

        status_code = getattr(exc, "status_code", None) or getattr(
            getattr(exc, "response", None), "status_code", None
        )
        text = str(exc).lower()

        if status_code == 401 or any(
            term in text for term in ("authentication", "unauthorized", "api key", "invalid_api_key")
        ):
            return InvalidApiKeyError(
                "Your OpenRouter API key was rejected. Double-check it in "
                "Settings and make sure it hasn't expired or been revoked.",
            )

        if status_code == 429 or "rate limit" in text or "too many requests" in text:
            return RateLimitedError(
                "You've hit OpenRouter's rate limit. Wait a moment and try again.",
                retryable=True,
            )

        if (
            "timeout" in text
            or "connection" in text
            or isinstance(exc, (ConnectionError, TimeoutError))
        ):
            return ConnectionFailedError(
                "Couldn't reach OpenRouter. Check your internet connection and try again.",
                retryable=True,
            )

        return AgentError(
            "Something went wrong talking to the AI model. Please try again.",
            retryable=True,
        )

    def invoke(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        chat_history: Optional[List[BaseMessage]] = None,
    ) -> str:
        """
        Executes a single inference call with context, prompt, and optional
        screenshot. Raises a typed AgentError (never a raw SDK exception) on
        failure, with a message that's already safe to show in the UI.
        """
        messages: List[BaseMessage] = [SystemMessage(content=self.system_prompt)]

        if chat_history:
            messages.extend(chat_history)

        user_message = self.build_multimodal_message(prompt, image_path)
        messages.append(user_message)

        try:
            response = self.llm.invoke(messages)
        except Exception as exc:
            raise self._classify_error(exc) from exc

        return response.content