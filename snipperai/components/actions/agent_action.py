import os
from typing import Optional

from snipperai.cloud.agent import AgentError, SnipperAgent


class AgentActionResult:
    """Outcome of a single AgentAction.execute() call.
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
            return AgentActionResult(error=err)

        except Exception as exc:
            return AgentActionResult(
                error=AgentError(
                    "Something went wrong talking to the AI model. Please try again.",
                    retryable=True,
                )
            )