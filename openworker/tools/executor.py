from typing import Dict, Any, List, Optional, Callable
import json
from mcp.client.session import ClientSession

class ToolExecutor:
    def __init__(self, clients: Dict[str, ClientSession], confirmation_callback: Optional[Callable[[str], Any]] = None):
        """
        Args:
            clients: Dict mapping server_name -> initialized MCP ClientSession.
            confirmation_callback: Async function to ask user for permission.
        """
        self.clients = clients
        self.confirmation_callback = confirmation_callback
        self.available_tools: List[Dict[str, Any]] = []
        self.tool_map: Dict[str, str] = {}  # Maps tool_name -> client_name

    async def initialize(self):
        """Fetch available tools from ALL MCP servers."""
        self.available_tools = []
        self.tool_map = {}
        
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

    def get_tools_definitions(self) -> List[Dict[str, Any]]:
        return self.available_tools

    async def execute_tool(self, tool_call: Any) -> str:
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)
        
        # Intercept Sensitive Tools
        # Intercept Sensitive Tools
        SENSITIVE_TOOLS = {"write_file", "index_folder", "reset_knowledge_base"}
        if fn_name in SENSITIVE_TOOLS and self.confirmation_callback:
            # Generate Summary
            from openworker.agents.summarizer import SummarizerAgent
            action_summary_agent = SummarizerAgent()
            # Do this in executor to avoid blocking if sync
            import asyncio
            summary = await asyncio.get_event_loop().run_in_executor(None, lambda: action_summary_agent.summarize_plan(fn_name, fn_args))
            
            prompt = f"\n[bold yellow]ACTION REQUIRED[/bold yellow]\n{summary}\n\nExecute this action?"
            
            approved = await self.confirmation_callback(prompt)
            if not approved:
                return "User denied permission."

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
