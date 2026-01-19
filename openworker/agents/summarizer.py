from openworker.core.llm import LLMClient
from openworker.prompts.action_summary import ACTION_SUMMARY_PROMPT
from openworker.agents.base_agent import BaseAgent
import json

class SummarizerAgent(BaseAgent):
    def __init__(self):
        self.llm = LLMClient(model="z-ai/glm-4.5-air:free") 

    def summarize_plan(self, tool_name: str, args: dict) -> str:
        """
        Uses LLM to summarize what a tool call will do.
        """
        user_content = f"Tool: {tool_name}\nArguments: {json.dumps(args, indent=2)}"
        
        try:
            message = self.llm.chat(
                messages=[
                    {"role": "system", "content": ACTION_SUMMARY_PROMPT},
                    {"role": "user", "content": user_content}
                ]
            )
            return message.content.strip()
        except Exception as e:
            return f"Execute tool '{tool_name}' with args: {str(args)}"
