import os
from typing import Optional
from snipperai.cloud.agent import SnipperAgent


class AgentAction:
    """Action component for running AI multimodal analysis on a captured snippet."""
    
    def __init__(self, agent: Optional[SnipperAgent] = None):
        self._agent = agent

    def execute(
        self, 
        image_path: str, 
        prompt: str = "Explain what is shown in this snippet concisely. Provide clear and actionable insights."
    ) -> str:
        if not os.path.exists(image_path):
            return "[Error: Screenshot buffer file not found.]"

        try:
            # Lazy initialization of agent (reads key from settings/config)
            if self._agent is None:
                self._agent = SnipperAgent()

            response = self._agent.invoke(prompt=prompt, image_path=image_path)
            return response if response else "[No response received from AI model.]"

        except ValueError as ve:
            return f"Configuration Error: {str(ve)}"
        except Exception as e:
            return f"AI Inference Error: {str(e)}"