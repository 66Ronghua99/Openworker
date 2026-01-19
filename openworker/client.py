import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from mcp.client.session import ClientSession

# Load env vars
load_dotenv()

from openworker.prompts.system import SYSTEM_PROMPT
from openworker.utils.decorators import trace_step

class ChatSession:
    def __init__(self, clients: Dict[str, Any], allowed_folders: List[str] = None):
        """
        Args:
            clients: Dict mapping server_name -> initialized MCP ClientSession.
            allowed_folders: List of paths the agent can access.
        """
        self.clients: Dict[str, ClientSession] = clients
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else None
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.model = "google/gemini-3-flash-preview" 
        
        self.allowed_folders = allowed_folders or []
        self._set_system_prompt()
        self.available_tools: List[Dict[str, Any]] = []
        self.tool_map: Dict[str, str] = {} # Maps tool_name -> client_name

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
        """Fetch available tools from ALL MCP servers."""
        self.available_tools = []
        self.tool_map = {}
        
        # Note: 'list_connected_servers' is now a terminal command '\list_servers'
        
        for name, session in self.clients.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    self.tool_map[tool.name] = name
                    self.available_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": f"[{name}] {tool.description}",
                            "parameters": tool.inputSchema
                        }
                    })
            except Exception as e:
                print(f"Error fetching tools from {name}: {e}")

    @trace_step("LLM Inference")
    async def _step_llm(self, history: List[Dict[str, Any]]) -> Any:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=history,
            tools=self.available_tools if self.available_tools else None,
        )
        return response.choices[0].message

    @trace_step("Tool Execution")
    async def _step_tool(self, tool_call: Any) -> str:
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)
        
        # MCP Tools
        if fn_name in self.tool_map:
            client_name = self.tool_map[fn_name]
            session: ClientSession = self.clients[client_name]
            try:
                tool_result = await session.call_tool(fn_name, fn_args)
                return str(tool_result.content) 
            except Exception as e:
                return f"Error executing tool {fn_name} on {client_name}: {str(e)}"
        else:
            return f"Error: Tool {fn_name} not found."

    async def chat(self, user_input: str) -> str:
        # Note: Input logging is now handled by the Trace on methods or can be kept explicit if preferred for top-level.
        # But for AOP purity, let's rely on the decorator for the steps.
        # However, the user input itself isn't a "step" function call unless we wrap it.
        # Let's keep one explicit log for User Input as it's the trigger.
        from openworker.utils.logger import get_logger
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
