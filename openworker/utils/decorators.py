from functools import wraps
import inspect
from typing import Callable, Any
from openworker.rag.security import get_guard
from openworker.utils.logger import get_logger

def secure_path(arg_name: str = "path"):
    """
    Decorator to validate a path argument against authorized folders.
    If validation fails, returns an error string (friendly for LLM tools).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inspect arguments to find the target parameter
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            path_val = bound_args.arguments.get(arg_name)
            
            if path_val:
                # If path_val is a list (e.g. for some future tool), check all? 
                # For now assuming string.
                if isinstance(path_val, str):
                    if not get_guard().validate_path(path_val):
                        return f"Error: Access denied. Path '{path_val}' is not in an authorized folder."
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

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
