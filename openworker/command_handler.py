from typing import Dict, Any, List, Optional
from rich.console import Console
from openworker.state import StateDB
from openworker.client import ChatSession

class CommandHandler:
    def __init__(self, console: Console, clients: Dict[str, Any], db: StateDB):
        self.console = console
        self.clients = clients
        self.db = db

    def handle_command(self, user_input: str, session: ChatSession) -> bool:
        """
        Parses and handles a command. Returns True if handled, False otherwise.
        """
        if not user_input.startswith("\\"):
            return False

        parts = user_input[1:].split()
        if not parts:
            return False
            
        cmd = parts[0]
        args = parts[1:]
        
        if cmd == "help":
            self.console.print("Commands:\n \\add <path>\n \\rm <path>\n \\folders\n \\list_servers\n \\clear")
        elif cmd == "list_servers":
            self.console.print(f"Connected Servers: {list(self.clients.keys())}")
        elif cmd == "folders":
            self.console.print(f"Tracked Folders: {self.db.list_folders()}")
        elif cmd == "add" and args:
            path = args[0]
            self.db.add_folder(path)
            self.console.print(f"Added {path}")
            # Update session context
            session.update_folders(self.db.list_folders())
        elif cmd == "rm" and args:
            path = args[0]
            self.db.remove_folder(path)
            self.console.print(f"Removed {path}")
            session.update_folders(self.db.list_folders())
        elif cmd == "clear":
            self.console.clear()
        else:
            self.console.print(f"Unknown command: {cmd}")
            
        return True
