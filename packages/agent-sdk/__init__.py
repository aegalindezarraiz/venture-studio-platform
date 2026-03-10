"""Agent SDK - base classes and types for AI Venture Studio OS agents."""
from packages.agent_sdk.types import AgentContext, AgentResult, AgentStatus
from packages.agent_sdk.base_agent import BaseAgent
from packages.agent_sdk.base import NotionAgentBase          # ← ADN con Notion integrado
from packages.agent_sdk.decorators import agent, tool

__all__ = [
    # Clase base con Notion — usar esta para todos los 500 agentes
    "NotionAgentBase",
    # Clase base simple — sin Notion
    "BaseAgent",
    # Tipos
    "AgentContext", "AgentResult", "AgentStatus",
    # Decoradores
    "agent", "tool",
]
