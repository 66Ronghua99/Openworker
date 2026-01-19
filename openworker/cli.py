import asyncio
import typer
import json
from rich.console import Console
from rich.markdown import Markdown
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from openworker.client import ChatSession
from contextlib import AsyncExitStack
import os

app = typer.Typer()
console = Console()

async def interactive_loop():
    console.print("[bold green]Starting MacOpenworker...[/bold green]")
    
    # Load Config
    config_path = "mcp_config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        # Default config if missing
        config = {
            "servers": {
                "macopenworker": {
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

        chat = ChatSession(clients)
        await chat.initialize()
        
        console.print(f"[bold blue]Available Tools:[/bold blue] {[t['function']['name'] for t in chat.available_tools]}")
        console.print("Type 'exit' or 'quit' to close.")

        while True:
            user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\n> ")
            if user_input.lower() in ["exit", "quit", "/quit"]:
                break
            
            if not user_input.strip():
                continue

            # Show a spinner while thinking
            with console.status("[bold green]Thinking...[/bold green]"):
                response = await chat.chat(user_input)
            
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
