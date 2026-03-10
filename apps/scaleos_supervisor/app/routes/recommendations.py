"""Recomendaciones tácticas generadas con Claude para cada startup."""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6")


class RecommendationRequest(BaseModel):
    startup_id: str
    startup_name: str
    stage: str
    industry: str
    mrr: float = 0
    at_risk_okrs: list[str] = []


@router.post("")
def generate_recommendations(payload: RecommendationRequest):
    """
    Genera recomendaciones tácticas accionables para una startup
    basándose en su etapa, OKRs en riesgo y métricas actuales.
    """
    recommendations = []

    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            prompt = (
                f"Eres el supervisor de un AI Venture Studio. "
                f"Analiza esta startup y da 3 recomendaciones tácticas accionables:\n\n"
                f"- Nombre: {payload.startup_name}\n"
                f"- Etapa: {payload.stage}\n"
                f"- Industria: {payload.industry}\n"
                f"- MRR actual: ${payload.mrr:,.0f}\n"
                f"- OKRs en riesgo: {', '.join(payload.at_risk_okrs) or 'ninguno'}\n\n"
                "Formato de respuesta: lista numerada, cada item en una línea, máximo 2 oraciones por item."
            )
            msg = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            # Parsear líneas numeradas
            for line in raw.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    recommendations.append(line.lstrip("0123456789.-) ").strip())
        except Exception as e:
            raise HTTPException(502, f"Error LLM: {e}")
    else:
        # Modo demo sin API key
        recommendations = [
            f"Enfoca el {payload.stage} en retención antes de escalar adquisición.",
            "Implementa un ciclo semanal de feedback con los primeros 10 usuarios.",
            "Define una métrica norte y alinea todos los OKRs a ella.",
        ]

    # Escribir tasks en Notion por cada recomendación
    try:
        import httpx
        backend = os.environ.get("BACKEND_URL", "http://localhost:8000")
        for rec in recommendations:
            httpx.post(f"{backend}/notion/tasks", json={
                "name": rec[:200],
                "startup_id": payload.startup_id,
                "priority": "Alta",
                "created_by_agent": True,
            }, timeout=10)
    except Exception:
        pass

    return {
        "startup_id": payload.startup_id,
        "startup_name": payload.startup_name,
        "recommendations": recommendations,
        "count": len(recommendations),
    }


@router.get("/{startup_id}")
def get_recommendations(startup_id: str):
    """Recupera las tareas creadas por el supervisor para una startup."""
    try:
        import httpx
        backend = os.environ.get("BACKEND_URL", "http://localhost:8000")
        r = httpx.get(f"{backend}/notion/tasks", params={
            "startup_id": startup_id,
            "status": "Backlog",
        }, timeout=10)
        tasks = r.json().get("tasks", [])
        agent_tasks = [t for t in tasks if "Agente" in t.get("name", "") or True]
        return {"startup_id": startup_id, "tasks": agent_tasks, "total": len(agent_tasks)}
    except Exception as e:
        return {"startup_id": startup_id, "tasks": [], "error": str(e)}
