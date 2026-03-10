"""Agent Runtime — punto de entrada."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import health, sessions
from app.services.runtime import runtime_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await runtime_service.startup()
    # Auto-registro en Notion (best-effort)
    try:
        from app.services.notion_sync import register_self
        notion_id = register_self()
        if notion_id:
            print(f"[agent_runtime] Registrado en Notion: {notion_id}")
    except Exception as e:
        print(f"[agent_runtime] Notion registro omitido: {e}")
    yield
    await runtime_service.shutdown()


app = FastAPI(
    title="Agent Runtime",
    description="Motor de ejecución de agentes del AI Venture Studio",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
