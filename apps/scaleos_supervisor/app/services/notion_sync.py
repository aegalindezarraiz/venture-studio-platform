"""
Sincronización del ScaleOS Supervisor con Notion.
Lee OKRs, actualiza su status y genera Weekly Reviews automáticamente.
"""
import os
import httpx
from datetime import datetime

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


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


def get_at_risk_okrs(startup_id: str | None = None) -> list[dict]:
    """Obtiene OKRs en estado 'At risk' u 'Off track'."""
    all_okrs = []
    for status in ("At risk", "Off track"):
        result = _get("/okrs", {"startup_id": startup_id or "", "status": status})
        all_okrs.extend(result.get("okrs", []))
    return all_okrs


def mark_okr_off_track(okr_id: str, progress: float) -> dict:
    return _patch(f"/okrs/{okr_id}", {"status": "Off track", "progress": progress})


def mark_okr_on_track(okr_id: str, progress: float) -> dict:
    return _patch(f"/okrs/{okr_id}", {"status": "On track", "progress": progress})


def compute_studio_health(startups: list[dict]) -> float:
    """
    Calcula un health score del studio como promedio de scores de startups.
    Si no hay scores, retorna 50.0 como baseline neutral.
    """
    scores = [s.get("score") for s in startups if s.get("score") is not None]
    return round(sum(scores) / len(scores), 1) if scores else 50.0


def push_weekly_review(
    startups: list[dict],
    highlights: str,
    blockers: str,
) -> dict:
    """Crea una Weekly Review en Notion con el health score calculado."""
    week = datetime.utcnow().strftime("Semana %W — %Y")
    health = compute_studio_health(startups)
    startup_ids = [s["id"] for s in startups if s.get("id")]

    return _post("/weekly-reviews", {
        "week_name": week,
        "highlights": highlights,
        "blockers": blockers,
        "health_score": health,
        "startup_ids": startup_ids,
    })


def auto_weekly_review() -> dict:
    """
    Genera automáticamente la Weekly Review del studio.
    Lee todas las startups activas y construye un resumen.
    """
    result = _get("/startups", {"status": "Activa"})
    startups = result.get("startups", [])

    if not startups:
        return {"error": "No hay startups activas"}

    at_risk = get_at_risk_okrs()
    highlights_lines = [f"• {s['name']} — Stage: {s.get('stage', '?')}, MRR: ${s.get('mrr') or 0:,.0f}" for s in startups]
    blockers_lines = [f"• OKR en riesgo: {o['name']}" for o in at_risk[:5]]

    return push_weekly_review(
        startups=startups,
        highlights="\n".join(highlights_lines) or "Sin highlights esta semana.",
        blockers="\n".join(blockers_lines) or "Sin blockers críticos.",
    )
