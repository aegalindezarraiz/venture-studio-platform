import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
_opportunities: dict[str, dict] = {}


class OpportunityCreate(BaseModel):
    startup_id: str
    domain: str
    keywords: list[str]
    competitors: list[str] = []


@router.post("", status_code=201)
async def create_opportunity(payload: OpportunityCreate):
    opp_id = str(uuid.uuid4())
    opp = {
        "id": opp_id,
        "status": "pending",
        "startup_id": payload.startup_id,
        "domain": payload.domain,
        "keywords": payload.keywords,
        "competitors": payload.competitors,
        "results": None,
    }
    _opportunities[opp_id] = opp
    # TODO: encolar análisis real
    return opp


@router.get("/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    opp = _opportunities.get(opportunity_id)
    if not opp:
        raise HTTPException(404, "Oportunidad no encontrada")
    return opp
