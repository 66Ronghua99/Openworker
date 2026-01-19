"""
Global configuration paths for Openworker.
All data is stored in ~/.openworker/ by default.
"""
from pathlib import Path
import os

# Base directory: ~/.openworker/
OPENWORKER_HOME = Path(os.environ.get("OPENWORKER_HOME", Path.home() / ".openworker"))

# Ensure directory exists
OPENWORKER_HOME.mkdir(parents=True, exist_ok=True)

# Specific paths
CHROMA_PATH = OPENWORKER_HOME / "chroma"
DB_PATH = OPENWORKER_HOME / "openworker.db"
CONFIG_PATH = OPENWORKER_HOME / "mcp_config.json"
ENV_PATH = OPENWORKER_HOME / ".env"

def get_default_config() -> dict:
    """Returns default MCP config if none exists."""
    return {
        "servers": {
            "openworker": {
                "command": "uv",
                "args": ["run", "python", "-m", "openworker.server"],
                "env": {}
            }
        }
    }