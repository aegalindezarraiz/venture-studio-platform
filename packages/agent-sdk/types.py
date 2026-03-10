"""Core types for the Agent SDK."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class AgentStatus(str, Enum):
    IDLE    = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR   = "error"
    TIMEOUT = "timeout"

@dataclass
class AgentContext:
    task_id:    str
    agent_id:   str
    org_id:     Optional[str]      = None
    startup_id: Optional[str]      = None
    payload:    dict[str, Any]     = field(default_factory=dict)
    memory:     dict[str, Any]     = field(default_factory=dict)
    metadata:   dict[str, Any]     = field(default_factory=dict)
    created_at: datetime           = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class AgentResult:
    task_id:      str
    agent_id:     str
    status:       AgentStatus
    output:       Any               = None
    error:        Optional[str]     = None
    duration_ms:  Optional[int]     = None
    tokens_used:  Optional[int]     = None
    metadata:     dict[str, Any]    = field(default_factory=dict)
    completed_at: datetime          = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "agent_id": self.agent_id,
            "status": self.status.value, "output": self.output, "error": self.error,
            "duration_ms": self.duration_ms, "tokens_used": self.tokens_used,
            "metadata": self.metadata, "completed_at": self.completed_at.isoformat(),
        }
