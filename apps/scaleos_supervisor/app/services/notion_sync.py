"""Sincronización del ScaleOS Supervisor con Notion."""
import os
import httpx
from datetime import datetime

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
_agent_notion_id: str | None = None


def _get(path: str, params: dict = {}) -> dict:
    try:
        r = httpx.get(f"{BACKEND_URL}/notion{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def _post(path: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{BACKEND_URL}/notion{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def _patch(path: str, payload: dict) -> dict:
    try:
        r = httpx.patch(f"{BACKEND_URL}/notion{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def register_self() -> str | None:
    global _agent_notion_id
    result = _post("/agents", {
        "name": "ScaleOS Supervisor",
        "type": "Supervisor",
        "service_url": os.environ.get("SCALEOS_SUPERVISOR_URL", "http://scaleos_supervisor:8002"),
        "model": os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6"),
    })
    _agent_notion_id = result.get("id")
    return _agent_notion_id


def get_all_startups() -> list[dict]:
    return _get("/startups", {"status": "Activa"}).get("startups", [])


def get_at_risk_okrs(startup_id: str | None = None) -> list[dict]:
    okrs = []
    for status in ("At risk", "Off track"):
        params = {"status": status}
        if startup_id:
            params["startup_id"] = startup_id
        okrs.extend(_get("/okrs", params).get("okrs", []))
    return okrs


def flag_okr(okr_id: str, status: str, progress: float) -> dict:
    return _patch(f"/okrs/{okr_id}", {"status": status, "progress": progress})


def create_recovery_task(okr_name: str, startup_id: str) -> dict:
    return _post("/tasks", {
        "name": f"Revisar y replantear: {okr_name}",
        "startup_id": startup_id,
        "priority": "Alta",
        "created_by_agent": True,
        "agent_id": _agent_notion_id,
    })


def compute_health(startups: list[dict]) -> float:
    scores = [s.get("score") for s in startups if s.get("score") is not None]
    return round(sum(scores) / len(scores), 1) if scores else 50.0


def push_weekly_review(startups: list[dict], at_risk_okrs: list[dict]) -> dict:
    week = datetime.utcnow().strftime("Semana %W — %Y")
    highlights = "\n".join(
        f"• {s['name']} — Stage: {s.get('stage','?')}  MRR: ${s.get('mrr') or 0:,.0f}"
        for s in startups
    ) or "Sin startups activas."
    blockers = "\n".join(
        f"• OKR en riesgo [{o.get('status')}]: {o['name']}"
        for o in at_risk_okrs[:5]
    ) or "Sin OKRs en riesgo."
    return _post("/weekly-reviews", {
        "week_name": week,
        "highlights": highlights,
        "blockers": blockers,
        "health_score": compute_health(startups),
        "startup_ids": [s["id"] for s in startups if s.get("id")],
    })
