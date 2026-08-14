import base64
from typing import Optional, List, Union
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openrouter import ChatOpenRouter
from snipperai.config import settings


class SnipperAgent:
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: str = "openai/gpt-4o-mini", 
        temperature: float = 0.7
    ):
        """
        Initializes the agent. Accepts a user-provided API key, 
        falling back to local Settings if not explicitly provided.
        """
        resolved_key = api_key or getattr(settings, "openrouter_api_key", None)
        print(f"Initialized SnipperAgent with api_key: {resolved_key[:5]}...")
        if not resolved_key:
            raise ValueError(
                "OpenRouter API key missing. Please provide a key in settings or pass it directly."
            )

        self.llm = ChatOpenRouter(
            api_key=resolved_key,  
            model=model_name,      
            temperature=temperature
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
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        ]
        return HumanMessage(content=content)

    def invoke(
        self, 
        prompt: str, 
        image_path: Optional[str] = None, 
        chat_history: Optional[List[BaseMessage]] = None
    ) -> str:
        """
        Executes a single inference call with context, prompt, and optional screenshot.
        """
        messages: List[BaseMessage] = [SystemMessage(content=self.system_prompt)]
        
        if chat_history:
            messages.extend(chat_history)
            
        user_message = self.build_multimodal_message(prompt, image_path)
        messages.append(user_message)

        response = self.llm.invoke(messages)
        return response.content