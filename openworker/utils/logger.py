import logging
import os
from datetime import datetime

class AgentLogger:
    def __init__(self, log_dir: str = "logs"):
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(log_dir, f"agent_trace_{timestamp}.log")
        
        self.logger = logging.getLogger("agent_logger")
        self.logger.setLevel(logging.INFO)
        
        # File Handler
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)

    def log_input(self, user_input: str):
        self.logger.info(f"USER INPUT: {user_input}")

    def log_thought(self, thought: str):
        self.logger.info(f"AGENT THOUGHT: {thought}")

    def log_tool_call(self, tool_name: str, args: dict):
        self.logger.info(f"TOOL CALL: {tool_name} | Args: {args}")

    def log_tool_result(self, tool_name: str, result: str):
        # Truncate long results
        preview = result[:500] + "..." if len(result) > 500 else result
        self.logger.info(f"TOOL RESULT ({tool_name}): {preview}")

    def log_response(self, response: str):
        self.logger.info(f"AGENT RESPONSE: {response}")

# Singleton
_logger = None
def get_logger():
    global _logger
    if _logger is None:
        _logger = AgentLogger()
    return _logger
