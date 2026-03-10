import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.runtime import runtime_service

router = APIRouter()


class SessionCreate(BaseModel):
    agent_id: str
    objective_bundle: dict
    context: dict = {}


class SessionResponse(BaseModel):
    id: str
    agent_id: str
    status: str
    result: dict | None = None


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(payload: SessionCreate):
    session = await runtime_service.create_session(
        agent_id=payload.agent_id,
        objective_bundle=payload.objective_bundle,
        context=payload.context,
    )
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    session = runtime_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return session


@router.delete("/{session_id}", status_code=204)
async def cancel_session(session_id: str):
    ok = await runtime_service.cancel_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
