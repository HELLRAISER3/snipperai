import os
from typing import Optional
from snipperai.cloud.agent import SnipperAgent


class AgentAction:
    """Action component for running AI multimodal analysis on a captured snippet."""

    def __init__(self, agent: Optional[SnipperAgent] = None):
        self._agent = agent

    def execute(
        self,
        image_path: Optional[str] = None,
        prompt: str = "Explain what is shown in this snippet concisely. Provide clear and actionable insights.",
        chat_history: Optional[list] = None,
    ) -> str:
        if image_path:
            if not os.path.isfile(image_path):
                return "[Error: Screenshot buffer file not found.]"

        try:
            if self._agent is None:
                self._agent = SnipperAgent()

            response = self._agent.invoke(
                prompt=prompt,
                image_path=image_path,
                chat_history=chat_history,
            )
            return response if response else "[No response received from AI model.]"

        except ValueError as ve:
            return f"Configuration Error: {ve}"
        except Exception as exc:
            return f"AI Inference Error: {exc}"
