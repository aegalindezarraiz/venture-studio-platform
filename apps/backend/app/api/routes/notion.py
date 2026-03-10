"""
Rutas REST para operaciones sobre Notion.
Prefijo: /notion
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services import notion_service as ns

router = APIRouter()


# ── Startups ──────────────────────────────────────────────────────────────────

@router.get("/startups")
def list_startups(status: Optional[str] = Query(None, description="Filtrar por status: Activa, En pausa…")):
    try:
        return {"startups": ns.get_startups(status=status)}
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


@router.get("/startups/{startup_id}")
def get_startup(startup_id: str):
    try:
        return ns.get_startup(startup_id)
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


@router.patch("/startups/{startup_id}/score")
def update_score(startup_id: str, score: float = Query(..., ge=0, le=100)):
    try:
        ns.update_startup_score(startup_id, score)
        return {"ok": True, "startup_id": startup_id, "score": score}
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


# ── OKRs ──────────────────────────────────────────────────────────────────────

@router.get("/okrs")
def list_okrs(
    startup_id: Optional[str] = None,
    status: Optional[str] = Query(None, description="On track | At risk | Off track | Completado"),
):
    try:
        return {"okrs": ns.get_okrs(startup_id=startup_id, status=status)}
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


class OKRCreate(BaseModel):
    name: str
    startup_id: str
    quarter: str
    type: str = "Objetivo"


@router.post("/okrs", status_code=201)
def create_okr(payload: OKRCreate):
    try:
        return ns.create_okr(payload.name, payload.startup_id, payload.quarter, payload.type)
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


class OKRUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[float] = None


@router.patch("/okrs/{okr_id}")
def update_okr(okr_id: str, payload: OKRUpdate):
    try:
        ns.update_okr(okr_id, status=payload.status, progress=payload.progress)
        return {"ok": True, "okr_id": okr_id}
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


# ── Tasks ─────────────────────────────────────────────────────────────────────

@router.get("/tasks")
def list_tasks(startup_id: Optional[str] = None, status: Optional[str] = None):
    try:
        return {"tasks": ns.get_tasks(startup_id=startup_id, status=status)}
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


class TaskCreate(BaseModel):
    name: str
    startup_id: Optional[str] = None
    okr_id: Optional[str] = None
    priority: str = "Media"
    created_by_agent: bool = False
    agent_id: Optional[str] = None


@router.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    try:
        return ns.create_task(
            name=payload.name,
            startup_id=payload.startup_id,
            okr_id=payload.okr_id,
            priority=payload.priority,
            created_by_agent=payload.created_by_agent,
            agent_id=payload.agent_id,
        )
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


# ── Briefs ────────────────────────────────────────────────────────────────────

class BriefCreate(BaseModel):
    name: str
    type: str
    content: str
    startup_id: Optional[str] = None
    agent_id: Optional[str] = None


@router.post("/briefs", status_code=201)
def create_brief(payload: BriefCreate):
    try:
        return ns.create_brief(
            name=payload.name,
            brief_type=payload.type,
            content=payload.content,
            startup_id=payload.startup_id,
            agent_id=payload.agent_id,
        )
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


# ── Experiments ───────────────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    name: str
    hypothesis: str
    channel: str
    metric: str
    startup_id: Optional[str] = None
    brief_id: Optional[str] = None


@router.post("/experiments", status_code=201)
def create_experiment(payload: ExperimentCreate):
    try:
        return ns.create_experiment(
            name=payload.name,
            hypothesis=payload.hypothesis,
            channel=payload.channel,
            metric=payload.metric,
            startup_id=payload.startup_id,
            brief_id=payload.brief_id,
        )
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


# ── Agents ────────────────────────────────────────────────────────────────────

@router.get("/agents")
def list_agents(status: Optional[str] = "Activo"):
    try:
        return {"agents": ns.get_agents(status=status)}
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


class AgentUpsert(BaseModel):
    name: str
    type: str
    service_url: str
    model: str = "claude-sonnet-4-6"


@router.post("/agents", status_code=201)
def upsert_agent(payload: AgentUpsert):
    try:
        return ns.upsert_agent(payload.name, payload.type, payload.service_url, payload.model)
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


@router.post("/agents/{agent_id}/run")
def record_run(agent_id: str):
    try:
        ns.record_agent_run(agent_id)
        return {"ok": True, "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")


# ── Weekly Reviews ────────────────────────────────────────────────────────────

class WeeklyReviewCreate(BaseModel):
    week_name: str
    highlights: str
    blockers: str
    health_score: float
    startup_ids: list[str] = []


@router.post("/weekly-reviews", status_code=201)
def create_weekly_review(payload: WeeklyReviewCreate):
    try:
        return ns.create_weekly_review(
            week_name=payload.week_name,
            highlights=payload.highlights,
            blockers=payload.blockers,
            health_score=payload.health_score,
            startup_ids=payload.startup_ids,
        )
    except Exception as e:
        raise HTTPException(502, f"Error Notion: {e}")
