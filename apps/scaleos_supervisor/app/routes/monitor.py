"""
Rutas de monitoreo automático — ScaleOS Supervisor.
/monitor/okrs   → escanea OKRs en riesgo y crea tasks de recuperación
/monitor/weekly → genera Weekly Review automática del studio
"""
from fastapi import APIRouter
from app.services.notion_sync import (
    get_all_startups, get_at_risk_okrs,
    create_recovery_task, push_weekly_review,
    compute_health,
)

router = APIRouter()


@router.post("/okrs")
def monitor_okrs():
    """
    Escanea todos los OKRs en estado 'At risk' u 'Off track'.
    Por cada uno crea una tarea de recuperación en Notion.
    """
    at_risk = get_at_risk_okrs()
    tasks_created = []

    for okr in at_risk:
        okr_name = okr.get("name", "OKR sin nombre")
        # Buscar startup_id desde el OKR (si está en la relación)
        startup_id = okr.get("startup_id")  # disponible si la relación está configurada
        if startup_id:
            task = create_recovery_task(okr_name, startup_id)
            tasks_created.append({"okr": okr_name, "task_id": task.get("id")})

    return {
        "at_risk_count": len(at_risk),
        "tasks_created": len(tasks_created),
        "detail": tasks_created,
    }


@router.post("/weekly")
def generate_weekly_review():
    """
    Genera automáticamente la Weekly Review del studio:
    - Recopila startups activas y sus scores
    - Escanea OKRs en riesgo
    - Calcula health score del studio
    - Crea la review en 📅 Weekly Reviews de Notion
    """
    startups = get_all_startups()
    at_risk = get_at_risk_okrs()
    review = push_weekly_review(startups, at_risk)
    return {
        "review_id": review.get("id"),
        "review_name": review.get("name"),
        "startups_evaluated": len(startups),
        "okrs_at_risk": len(at_risk),
        "health_score": compute_health(startups),
        "notion_url": review.get("url"),
    }


@router.get("/status")
def studio_status():
    """Vista rápida del estado actual del studio."""
    startups = get_all_startups()
    at_risk = get_at_risk_okrs()
    return {
        "active_startups": len(startups),
        "okrs_at_risk": len(at_risk),
        "health_score": compute_health(startups),
        "startups": [
            {"name": s["name"], "stage": s.get("stage"), "mrr": s.get("mrr"), "score": s.get("score")}
            for s in startups
        ],
    }
