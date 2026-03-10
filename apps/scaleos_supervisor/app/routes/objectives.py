from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter()

# In-memory store (reemplazar con DB en producción)
_objectives: dict[str, dict] = {}


class ObjectiveCreate(BaseModel):
    startup_id: str
    title: str
    description: str
    target_metric: str
    target_value: float
    due_date: str


@router.get("")
async def list_objectives(startup_id: Optional[str] = None):
    items = list(_objectives.values())
    if startup_id:
        items = [o for o in items if o["startup_id"] == startup_id]
    return {"items": items, "total": len(items)}


@router.post("", status_code=201)
async def create_objective(payload: ObjectiveCreate):
    obj_id = str(uuid.uuid4())
    obj = {"id": obj_id, "status": "active", **payload.model_dump()}
    _objectives[obj_id] = obj
    return obj


@router.get("/{objective_id}")
async def get_objective(objective_id: str):
    obj = _objectives.get(objective_id)
    if not obj:
        from fastapi import HTTPException
        raise HTTPException(404, "Objetivo no encontrado")
    return obj
