"""Decorators for the Agent SDK."""
import functools, logging
from typing import Callable

def agent(agent_id: str, name: str, category: str, priority: int = 2):
    def decorator(func: Callable):
        func._agent_id = agent_id
        func._agent_name = name
        func._agent_category = category
        func._agent_priority = priority
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def tool(name: str, description: str):
    def decorator(func: Callable):
        func._tool_name = name
        func._tool_description = description
        func._is_tool = True
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
