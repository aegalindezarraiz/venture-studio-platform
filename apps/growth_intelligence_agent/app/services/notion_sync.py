"""Sincronización del Growth Intelligence Agent con Notion."""
import os
import re
import httpx
from datetime import datetime

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
_agent_notion_id: str | None = None


def _post(path: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{BACKEND_URL}/notion{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def register_self() -> str | None:
    global _agent_notion_id
    result = _post("/agents", {
        "name": "Growth Intelligence Agent",
        "type": "Growth",
        "service_url": os.environ.get("GROWTH_INTELLIGENCE_URL", "http://growth_intelligence_agent:8004"),
        "model": os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6"),
    })
    _agent_notion_id = result.get("id")
    return _agent_notion_id


def push_brief(startup_id: str, startup_name: str, brief_content: str) -> dict:
    week = datetime.utcnow().strftime("%Y-W%W")
    return _post("/briefs", {
        "name": f"Growth Brief — {startup_name} ({week})",
        "type": "Growth",
        "content": brief_content,
        "startup_id": startup_id,
        "agent_id": _agent_notion_id,
    })


_ACTIONABLE = re.compile(
    r"^[\-\*\•]?\s*\[?\s*\]?\s*(.{10,200})$",
    re.MULTILINE,
)
_ACTION_VERBS = {
    "implementa", "crea", "lanza", "define", "configura",
    "prueba", "analiza", "contacta", "publica", "diseña",
    "mide", "optimiza", "automatiza", "escala", "valida",
}


def push_tasks_from_brief(brief_content: str, startup_id: str, brief_notion_id: str | None = None) -> list[dict]:
    """Extrae hasta 5 tasks accionables del brief y las crea en ✅ Tasks."""
    created = []
    for m in _ACTIONABLE.finditer(brief_content):
        line = m.group(1).strip()
        if any(v in line.lower() for v in _ACTION_VERBS):
            result = _post("/tasks", {
                "name": line[:200],
                "startup_id": startup_id,
                "priority": "Alta",
                "created_by_agent": True,
                "agent_id": _agent_notion_id,
            })
            if "id" in result:
                created.append(result)
            if len(created) >= 5:
                break
    return created
