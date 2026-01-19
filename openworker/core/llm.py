import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

class LLMClient:
    def __init__(self, model: str = "google/gemini-3-flash-preview"):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else None
        self.model = model
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> ChatCompletionMessage:
        """
        Synchronous chat completion.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )
        return response.choices[0].message
