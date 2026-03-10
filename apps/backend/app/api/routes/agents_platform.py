"""
/agents — Catálogo de los 500 agentes AI del Venture Studio.
Endpoints: listado filtrado/paginado, detalle por ID, resumen por categoría,
y seed hacia Notion.
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional

from packages.agents.registry import get_all, get_by_id, get_summary, seed_to_notion

router = APIRouter()


@router.get(
    "",
    summary="Catálogo de agentes",
    description=(
        "Lista los 500 agentes con filtrado por categoría, prioridad y búsqueda de texto. "
        "Devuelve resultados paginados (máx. 100 por página)."
    ),
)
async def list_agents(
    category: Optional[str] = Query(None, description="executive | product | engineering | growth | data | security | osint"),
    priority: Optional[int] = Query(None, ge=1, le=3, description="1=crítico, 2=normal, 3=soporte"),
    search: Optional[str] = Query(None, min_length=2, description="Búsqueda en nombre, rol y descripción"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    return get_all(category=category, priority=priority, search=search, page=page, page_size=page_size)


@router.get(
    "/summary",
    summary="Resumen por categoría",
    description="Conteos por categoría con estado en tiempo real (ready/checked/unchecked).",
)
async def agents_summary():
    return get_summary()


@router.get(
    "/{agent_id}",
    summary="Detalle de un agente",
    description="Devuelve la definición completa de un agente por su ID (slug).",
)
async def get_agent(agent_id: str):
    agent = get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' no encontrado")
    return agent


@router.post(
    "/seed/notion",
    summary="Registrar todos los agentes en Notion",
    description=(
        "Crea o actualiza las 500 entradas en la DB 🤖 Agents de Notion. "
        "Ejecuta en background; el resultado se devuelve al finalizar si el cliente espera, "
        "o se puede lanzar como tarea de background."
    ),
)
async def seed_agents_to_notion(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(10, ge=1, le=50, description="Requests por batch antes de pausar"),
    run_in_background: bool = Query(False, description="Si True, ejecuta en background y retorna inmediatamente"),
):
    if run_in_background:
        background_tasks.add_task(_seed_bg, batch_size)
        return {"status": "started", "message": "Seed lanzado en background. Revisa los logs para el resultado."}

    # Ejecución síncrona (puede tardar ~30 s para 500 agentes)
    result = seed_to_notion(batch_size=batch_size)
    return {"status": "done", **result}


def _seed_bg(batch_size: int):
    import logging
    log = logging.getLogger("agent-seed")
    try:
        result = seed_to_notion(batch_size=batch_size)
        log.info(f"Seed completado: {result}")
    except Exception as e:
        log.error(f"Error en seed: {e}")
