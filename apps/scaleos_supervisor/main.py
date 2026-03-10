from fastapi import FastAPI
from app.routes import health, objectives, recommendations

app = FastAPI(
    title="ScaleOS Supervisor",
    description="Supervisor de OKRs y recomendaciones tácticas para startups",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(objectives.router, prefix="/objectives", tags=["objectives"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
