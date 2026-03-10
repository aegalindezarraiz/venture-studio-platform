"""Task Runtime - Redis-backed async task queue."""
import json, logging, os, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

log = logging.getLogger("task-runtime")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

class TaskStatus(str, Enum):
    PENDING   = "pending"
    QUEUED    = "queued"
    RUNNING   = "running"
    SUCCESS   = "success"
    FAILED    = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id:       str             = field(default_factory=lambda: str(uuid.uuid4()))
    type:     str             = ""
    payload:  dict[str, Any]  = field(default_factory=dict)
    status:   TaskStatus      = TaskStatus.PENDING
    result:   Optional[Any]   = None
    error:    Optional[str]   = None
    priority: int             = 2
    retries:  int             = 0

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "payload": self.payload,
                "status": self.status.value, "result": self.result, "error": self.error,
                "priority": self.priority, "retries": self.retries}

class TaskRuntime:
    def __init__(self, queue: str = "venture:tasks"):
        self.queue = queue
        self._handlers: dict[str, Callable] = {}

    def _r(self):
        import redis
        return redis.from_url(REDIS_URL, decode_responses=True)

    def register(self, task_type: str):
        def decorator(func):
            self._handlers[task_type] = func
            return func
        return decorator

    def submit(self, task: Task) -> str:
        task.status = TaskStatus.QUEUED
        r = self._r()
        r.setex(f"task:{task.id}", 86400, json.dumps(task.to_dict()))
        r.lpush(self.queue, task.id)
        r.close()
        return task.id

    def get_status(self, task_id: str) -> Optional[dict]:
        try:
            r = self._r()
            data = r.get(f"task:{task_id}")
            r.close()
            return json.loads(data) if data else None
        except Exception:
            return None

    def queue_depth(self) -> int:
        try:
            r = self._r()
            depth = r.llen(self.queue)
            r.close()
            return depth
        except Exception:
            return -1
