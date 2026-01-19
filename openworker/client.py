import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from mcp.client.session import ClientSession

# Load env vars
load_dotenv()

from openworker.prompts.system import SYSTEM_PROMPT

class ChatSession:
    def __init__(self, clients: Dict[str, Any]):
        """
        Args:
            clients: Dict mapping server_name -> initialized MCP ClientSession.
        """
        self.clients: Dict[str, ClientSession] = clients
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else None
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.model = "google/gemini-2.0-flash-001" # Default to a good model, or configurable
        
        self.history: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.available_tools: List[Dict[str, Any]] = []
        self.tool_map: Dict[str, str] = {} # Maps tool_name -> client_name

    async def initialize(self):
        """Fetch available tools from ALL MCP servers."""
        self.available_tools = []
        self.tool_map = {}
        
        # Add the 'list_connected_servers' client-side tool
        self.available_tools.append({
            "type": "function",
            "function": {
                "name": "list_connected_servers",
                "description": "List all currently connected MCP servers.",
                "parameters": {"type": "object", "properties": {}}
            }
        })
        
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

    async def chat(self, user_input: str) -> str:
        from openworker.utils.logger import get_logger
        logger = get_logger()
        logger.log_input(user_input)
        
        self.history.append({"role": "user", "content": user_input})
        
        # Loop for tool calls
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                tools=self.available_tools if self.available_tools else None,
            )
            
            message = response.choices[0].message
            # Log the raw response/thought process if available, or just the intent
            if message.content:
                logger.log_thought(message.content)

            self.history.append(message)
            
            if not message.tool_calls:
                logger.log_response(message.content)
                return message.content
            
            # Handle tool calls
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                logger.log_tool_call(fn_name, fn_args)
                
                content = ""
                # Special Client-side tools
                if fn_name == "list_connected_servers":
                    content = "Connected Servers:\n" + "\n".join([f"- {name}" for name in self.clients.keys()])
                # MCP Tools
                elif fn_name in self.tool_map:
                    client_name = self.tool_map[fn_name]
                    session: ClientSession = self.clients[client_name]
                    try:
                        tool_result = await session.call_tool(fn_name, fn_args)
                        content = str(tool_result.content) 
                    except Exception as e:
                        content = f"Error executing tool {fn_name} on {client_name}: {str(e)}"
                else:
                    content = f"Error: Tool {fn_name} not found."
                
                logger.log_tool_result(fn_name, content)

                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": content
                })
