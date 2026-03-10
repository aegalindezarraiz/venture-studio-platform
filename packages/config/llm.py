"""Configuración centralizada de proveedores LLM."""
import os
from enum import Enum


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


DEFAULT_PROVIDER = LLMProvider(os.environ.get("DEFAULT_LLM_PROVIDER", "anthropic"))
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6")

PROVIDER_MODELS = {
    LLMProvider.ANTHROPIC: [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ],
    LLMProvider.OPENAI: [
        "gpt-4o",
        "gpt-4o-mini",
    ],
}
