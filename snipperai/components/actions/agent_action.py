# snipperai/components/actions.py
import os
from typing import Optional

from snipperai.cloud.agent import AgentError, SnipperAgent


class AgentActionResult:
    """Outcome of a single AgentAction.execute() call.

    Deliberately not a plain string: keeping the success/error path typed
    means the UI layer can decide how to render an error (short, centered,
    with an "open Settings" hint for key problems) instead of receiving an
    error as if it were a normal AI response and running it through the
    full markdown renderer - which is how raw exception text was ending up
    visible in the chat window.
    """

    def __init__(self, text: Optional[str] = None, error: Optional[AgentError] = None):
        self.text = text
        self.error = error

    @property
    def ok(self) -> bool:
        return self.error is None


class AgentAction:
    def __init__(self, agent: Optional[SnipperAgent] = None):
        self._agent = agent

    def execute(
        self,
        image_path: Optional[str] = None,
        prompt: str = "Explain what is shown in this snippet concisely. Provide clear and actionable insights.",
        chat_history: Optional[list] = None,
    ) -> AgentActionResult:
        if image_path and not os.path.isfile(image_path):
            return AgentActionResult(
                error=AgentError("Couldn't find the screenshot file - try capturing again.")
            )

        try:
            if self._agent is None:
                self._agent = SnipperAgent()

            response = self._agent.invoke(
                prompt=prompt,
                image_path=image_path,
                chat_history=chat_history,
            )
            return AgentActionResult(text=response or "[No response received from the AI model.]")

        except AgentError as err:
            # Already a clean, user-safe message - pass it straight through.
            return AgentActionResult(error=err)

        except Exception as exc:
            # Anything unclassified: never leak the raw exception into the
            # UI. This is deliberately a generic message even though we
            # don't know exactly what failed - specifics get logged inside
            # SnipperAgent, not shown here.
            return AgentActionResult(
                error=AgentError(
                    "Something went wrong talking to the AI model. Please try again.",
                    retryable=True,
                )
            )