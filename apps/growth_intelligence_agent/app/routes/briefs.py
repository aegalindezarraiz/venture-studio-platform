import uuid
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic

router = APIRouter()
_briefs: dict[str, dict] = {}

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class BriefCreate(BaseModel):
    startup_id: str
    startup_name: str
    stage: str
    industry: str
    current_metrics: dict
    goals: list[str]


@router.post("", status_code=201)
async def create_brief(payload: BriefCreate):
    brief_id = str(uuid.uuid4())
    brief = {
        "id": brief_id,
        "status": "generating",
        "startup_id": payload.startup_id,
        "content": None,
    }
    _briefs[brief_id] = brief

    if ANTHROPIC_API_KEY:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = (
            f"Genera un brief de crecimiento para la startup '{payload.startup_name}' "
            f"en etapa {payload.stage}, industria {payload.industry}. "
            f"Métricas actuales: {payload.current_metrics}. "
            f"Objetivos: {payload.goals}. "
            "Incluye: canales prioritarios, tácticas accionables, KPIs a medir."
        )
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        brief["content"] = message.content[0].text
    else:
        brief["content"] = "Brief generado en modo demo (sin API key)."

    brief["status"] = "ready"
    return brief


@router.get("/{brief_id}")
async def get_brief(brief_id: str):
    brief = _briefs.get(brief_id)
    if not brief:
        raise HTTPException(404, "Brief no encontrado")
    return brief
