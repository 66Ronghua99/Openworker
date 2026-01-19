import logging
import os
import inspect
from datetime import datetime
from typing import Callable
from functools import wraps

class AgentLogger:
    def __init__(self, log_dir: str = ".logs"):
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
        preview = result[:2000] + "..." if len(result) > 2000 else result
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

def trace_step(step_name: str = None):
    """
    Decorator to log the entry and exit of a function step.
    Logs inputs and output result.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger()
            name = step_name or func.__name__
            
            # Simple repr of args for logging
            # (Be careful with huge objects, maybe truncate str representation)
            args_repr = [str(a)[:100] for a in args]
            kwargs_repr = {k: str(v)[:100] for k, v in kwargs.items()}
            
            # logger.logger.info(f"STEP_START: {name} | Args: {args_repr} {kwargs_repr}")
            
            try:
                result = await func(*args, **kwargs)
                logger.logger.info(f"STEP_END: {name} | Result: {str(result)[:500]}...")
                return result
            except Exception as e:
                logger.logger.error(f"STEP_ERROR: {name} | {str(e)}")
                raise e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger()
            name = step_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.logger.error(f"STEP_ERROR: {name} | {str(e)}")
                raise e

        # Basic async detection
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator