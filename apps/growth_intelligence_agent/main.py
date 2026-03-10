"""Growth Intelligence Agent — punto de entrada."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import health, briefs


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.services.notion_sync import register_self
        notion_id = register_self()
        if notion_id:
            print(f"[growth_intelligence] Registrado en Notion: {notion_id}")
    except Exception as e:
        print(f"[growth_intelligence] Notion registro omitido: {e}")
    yield


app = FastAPI(
    title="Growth Intelligence Agent",
    description="Genera briefs de crecimiento accionables con sincronización automática a Notion",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(briefs.router, prefix="/briefs", tags=["briefs"])
