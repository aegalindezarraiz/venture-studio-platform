"""Sincronización del Agent Runtime con Notion."""
import os
import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
_agent_notion_id: str | None = None  # se rellena al arrancar


def _post(path: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{BACKEND_URL}/notion{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def register_self() -> str | None:
    """Registra este agente en 🤖 Agents al arrancar. Devuelve el Notion page ID."""
    global _agent_notion_id
    result = _post("/agents", {
        "name": "Agent Runtime",
        "type": "Runtime",
        "service_url": os.environ.get("AGENT_RUNTIME_URL", "http://agent_runtime:8001"),
        "model": os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6"),
    })
    _agent_notion_id = result.get("id")
    return _agent_notion_id


def record_session(session_id: str, agent_id_notion: str | None, status: str, result_summary: str | None = None):
    """Registra ejecución del agente y crea tarea si el resultado lo merece."""
    aid = agent_id_notion or _agent_notion_id
    if aid:
        _post(f"/agents/{aid}/run", {})

    if status == "completed" and result_summary:
        _post("/tasks", {
            "name": f"Revisar resultado de sesión: {session_id[:8]}",
            "priority": "Media",
            "created_by_agent": True,
            "agent_id": aid,
        })
