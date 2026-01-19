import asyncio
import typer
import json
from rich.console import Console
from rich.markdown import Markdown
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from openworker.client import ChatSession
from openworker.tools.executor import ToolExecutor
from contextlib import AsyncExitStack
import os

app = typer.Typer()
console = Console()

# Global spinner state holder
SPINNER_STATE = []

async def async_confirm(question: str) -> bool:
    """Async wrapper for typer.confirm with spinner pause."""
    # Pause spinner if active
    active_status = SPINNER_STATE[0] if SPINNER_STATE else None
    if active_status:
        active_status.stop()
        
    try:
        # Force a new line before prompt
        # Render the rich text question
        console.print(question)
        # Ask for confirmation without repeating the text
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: typer.confirm("", default=False)
        )
    finally:
        # Resume spinner
        if active_status:
            active_status.start()

async def interactive_loop():
    console.print("[bold green]Starting Openworker...[/bold green]")
    
    # Load Config
    config_path = "mcp_config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        # Default config if missing
        config = {
            "servers": {
                "openworker": {
                    "command": "uv",
                    "args": ["run", "python", "-m", "openworker.server"],
                    "env": os.environ.copy()
                }
            }
        }

    async with AsyncExitStack() as stack:
        clients = {}
        
        # Connect to each server
        for name, cfg in config.get("servers", {}).items():
            env = os.environ.copy()
            if "env" in cfg:
                env.update(cfg["env"])
                
            server_params = StdioServerParameters(
                command=cfg["command"],
                args=cfg["args"],
                env=env
            )
            
            try:
                # Enter context manager for transport
                read, write = await stack.enter_async_context(stdio_client(server_params))
                # Enter context manager for session
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                clients[name] = session
                console.print(f"[green]Connected to server: {name}[/green]")
            except Exception as e:
                console.print(f"[red]Failed to connect to {name}: {e}[/red]")
        
        if not clients:
            console.print("[bold red]No servers connected. Exiting.[/bold red]")
            return

        from openworker.state import get_db
        db = get_db()
        
        # Initial Folder Load
        folders = db.list_folders()
        if folders:
            console.print(f"[bold blue]Active Folders:[/bold blue] {folders}")

        # Initialize ToolExecutor
        tool_executor = ToolExecutor(clients, confirmation_callback=async_confirm)
        
        chat = ChatSession(tool_executor, allowed_folders=folders)
        await chat.initialize()
        
        from openworker.command_handler import CommandHandler
        cmd_handler = CommandHandler(console, clients, db)

        console.print(f"[bold blue]Available Tools:[/bold blue] {[t['function']['name'] for t in tool_executor.get_tools_definitions()]}")
        console.print("Type 'exit' or use '\\' for commands (e.g. \\help).")

        while True:
            user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\n> ")
            if user_input.lower() in ["exit", "quit", "/quit"]:
                break
            
            if not user_input.strip():
                continue

            # Command Dispatcher
            if cmd_handler.handle_command(user_input, chat):
                continue

            # Show a spinner while thinking
            with console.status("[bold green]Thinking...[/bold green]") as status:
                SPINNER_STATE.append(status)
                try:
                    response = await chat.chat(user_input)
                finally:
                    if SPINNER_STATE:
                        SPINNER_STATE.pop()
            
            console.print(Markdown(response))

@app.command()
def start():
    """Start the interactive session."""
    try:
        asyncio.run(interactive_loop())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Goodbye![/bold yellow]")

if __name__ == "__main__":
    app()
