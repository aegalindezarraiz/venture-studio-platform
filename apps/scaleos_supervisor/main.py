"""ScaleOS Supervisor — punto de entrada."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import health, objectives, recommendations, monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.services.notion_sync import register_self
        notion_id = register_self()
        if notion_id:
            print(f"[scaleos_supervisor] Registrado en Notion: {notion_id}")
    except Exception as e:
        print(f"[scaleos_supervisor] Notion registro omitido: {e}")
    yield


app = FastAPI(
    title="ScaleOS Supervisor",
    description="Supervisor de OKRs y recomendaciones tácticas para startups",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(objectives.router, prefix="/objectives", tags=["objectives"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(monitor.router, prefix="/monitor", tags=["monitor"])
