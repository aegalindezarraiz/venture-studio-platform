"""Memory Engine - short-term (Redis) and long-term (Qdrant) memory for agents."""
import json, logging, os
from typing import Any, Optional

log = logging.getLogger("memory-engine")
REDIS_URL  = os.environ.get("REDIS_URL",  "redis://localhost:6379/0")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "venture_memory")

class MemoryEngine:
    def __init__(self, agent_id: str, org_id: Optional[str] = None):
        self.agent_id = agent_id
        self.org_id   = org_id
        self._redis   = None

    def _r(self):
        if not self._redis:
            import redis
            self._redis = redis.from_url(REDIS_URL, decode_responses=True)
        return self._redis

    def _ns(self, key: str) -> str:
        prefix = f"{self.org_id}:{self.agent_id}" if self.org_id else self.agent_id
        return f"mem:{prefix}:{key}"

    def remember(self, key: str, value: Any, ttl: int = 3600) -> None:
        try:
            self._r().setex(self._ns(key), ttl, json.dumps(value))
        except Exception as e:
            log.warning(f"remember error ({key}): {e}")

    def recall(self, key: str) -> Optional[Any]:
        try:
            data = self._r().get(self._ns(key))
            return json.loads(data) if data else None
        except Exception as e:
            log.warning(f"recall error ({key}): {e}")
            return None

    def forget(self, key: str) -> None:
        try:
            self._r().delete(self._ns(key))
        except Exception:
            pass

    def search_semantic(self, query: str, limit: int = 5) -> list[dict]:
        # TODO: implement with Qdrant + embeddings
        return []
