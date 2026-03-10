from fastapi import APIRouter, HTTPException

router = APIRouter()

# Mock de recomendaciones (conectar a LLM o lógica real)
_recommendations: dict[str, list] = {}


@router.get("/{startup_id}")
async def get_recommendations(startup_id: str):
    recs = _recommendations.get(startup_id, [])
    return {"startup_id": startup_id, "recommendations": recs, "total": len(recs)}
