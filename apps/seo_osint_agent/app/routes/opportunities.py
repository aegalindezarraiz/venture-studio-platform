"""
SEO & OSINT Agent — análisis de oportunidades con sincronización a Notion.
Cada oportunidad detectada genera automáticamente un Experiment en Notion.
"""
import uuid
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()
_opportunities: dict[str, dict] = {}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6")


class OpportunityCreate(BaseModel):
    startup_id: str
    startup_name: str
    domain: str
    keywords: list[str]
    competitors: list[str] = []


def _analyze_and_sync(opp: dict):
    """
    Tarea de fondo: analiza las keywords con Claude y sincroniza
    los resultados (experimentos + tasks) con Notion.
    """
    from app.services.notion_sync import push_seo_opportunity, push_competitor_signal

    startup_id = opp["startup_id"]
    startup_name = opp["startup_name"]

    # 1. Analizar keywords con LLM (o modo demo)
    keywords_analysis = []
    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            prompt = (
                f"Analiza estas keywords para la startup '{startup_name}' (dominio: {opp['domain']}):\n"
                f"Keywords: {', '.join(opp['keywords'])}\n"
                f"Competidores: {', '.join(opp['competitors']) or 'no especificados'}\n\n"
                "Para cada keyword devuelve: keyword, volumen estimado (número), dificultad 0-100. "
                "Formato JSON array: [{\"keyword\": \"...\", \"volume\": 0, \"difficulty\": 0}]"
            )
            msg = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            import json, re
            raw = msg.content[0].text
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                keywords_analysis = json.loads(match.group())
        except Exception:
            pass

    # Fallback demo si no hay análisis LLM
    if not keywords_analysis:
        keywords_analysis = [
            {"keyword": kw, "volume": 1000 * (i + 1), "difficulty": 30 + i * 10}
            for i, kw in enumerate(opp["keywords"])
        ]

    # 2. Crear Experiments en Notion por keyword
    experiments_created = []
    for kw_data in keywords_analysis:
        result = push_seo_opportunity(
            startup_id=startup_id,
            keyword=kw_data["keyword"],
            search_volume=kw_data.get("volume", 500),
            difficulty=kw_data.get("difficulty", 50),
            competitor=opp["competitors"][0] if opp["competitors"] else None,
        )
        if "id" in result:
            experiments_created.append(result["id"])

    # 3. Señales OSINT por competidor
    for competitor in opp["competitors"]:
        push_competitor_signal(
            startup_id=startup_id,
            competitor_name=competitor,
            signal_type="content",
            description=f"Competidor detectado en búsqueda de {', '.join(opp['keywords'][:2])}",
        )

    opp["status"] = "completed"
    opp["experiments_created"] = len(experiments_created)
    opp["keywords_analyzed"] = keywords_analysis


class OpportunityCreate(BaseModel):
    startup_id: str
    startup_name: str
    domain: str
    keywords: list[str]
    competitors: list[str] = []


@router.post("", status_code=201)
async def create_opportunity(payload: OpportunityCreate, background_tasks: BackgroundTasks):
    """
    Lanza un análisis SEO/OSINT en background.
    Resultado: experimentos creados en Notion con hipótesis y tasks accionables.
    """
    if not payload.keywords:
        raise HTTPException(400, "Debes incluir al menos una keyword")

    opp_id = str(uuid.uuid4())
    opp = {
        "id": opp_id,
        "status": "analyzing",
        "startup_id": payload.startup_id,
        "startup_name": payload.startup_name,
        "domain": payload.domain,
        "keywords": payload.keywords,
        "competitors": payload.competitors,
        "experiments_created": 0,
        "keywords_analyzed": [],
    }
    _opportunities[opp_id] = opp
    background_tasks.add_task(_analyze_and_sync, opp)
    return opp


@router.get("/{opportunity_id}")
def get_opportunity(opportunity_id: str):
    opp = _opportunities.get(opportunity_id)
    if not opp:
        raise HTTPException(404, "Oportunidad no encontrada")
    return opp


@router.get("")
def list_opportunities():
    return {"opportunities": list(_opportunities.values()), "total": len(_opportunities)}
