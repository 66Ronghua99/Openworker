from openworker.agents.react import ReactAgent
import os
import json
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from dotenv import load_dotenv
from openworker.agents.react import ReactAgent
from mcp.client.session import ClientSession

# Load env vars
load_dotenv()

from openworker.prompts.system import SYSTEM_PROMPT
from openworker.utils.logger import trace_step, get_logger

from openworker.tools.executor import ToolExecutor

from openworker.core.llm import LLMClient

class ChatSession(ReactAgent):
    def __init__(self, tool_executor: ToolExecutor, allowed_folders: List[str] = None):
        """
        Args:
            tool_executor: Initialized ToolExecutor.
            allowed_folders: List of paths the agent can access.
        """
        self.tool_executor = tool_executor
        self.llm = LLMClient()
        
        self.allowed_folders = allowed_folders or []
        self._set_system_prompt()

    def _set_system_prompt(self):
        folder_ctx = "\nYou have access to files in these folders:\n" + "\n".join(f"- {p}" for p in self.allowed_folders)
        content = SYSTEM_PROMPT + folder_ctx
        self.history: List[Dict[str, Any]] = [
            {"role": "system", "content": content}
        ]

    # Logic not very sound, it will remove all the dialogues, but works for now
    def update_folders(self, folders: List[str]):
        self.allowed_folders = folders
        self._set_system_prompt()

    async def initialize(self):
        """Fetch available tools from ToolExecutor."""
        await self.tool_executor.initialize()

    @trace_step("LLM Inference")
    async def _step_llm(self, history: List[Dict[str, Any]]) -> Any:
        # Run blocking LLM call in executor to avoid blocking the loop
        import asyncio
        loop = asyncio.get_event_loop()
        
        tools = self.tool_executor.get_tools_definitions() if self.tool_executor.get_tools_definitions() else None
        
        return await loop.run_in_executor(
            None,
            lambda: self.llm.chat(messages=history, tools=tools)
        )

    @trace_step("Tool Execution")
    async def _step_tool(self, tool_call: Any) -> str:
        return await self.tool_executor.execute_tool(tool_call)

    async def chat(self, user_input: str) -> str:
        # Note: Input logging is now handled by the Trace on methods or can be kept explicit if preferred for top-level.
        # But for AOP purity, let's rely on the decorator for the steps.
        # However, the user input itself isn't a "step" function call unless we wrap it.
        # Let's keep one explicit log for User Input as it's the trigger.
        get_logger().log_input(user_input)
        
        self.history.append({"role": "user", "content": user_input})
        
        while True:
            # 1. LLM Step
            message = await self._step_llm(self.history)
            self.history.append(message)
            
            # Log LLM Response
            if not message.tool_calls:
                get_logger().log_response(message.content)
                return message.content
            
            # 2. Tool Step
            for tool_call in message.tool_calls:
                content = await self._step_tool(tool_call)
                
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": content
                })
