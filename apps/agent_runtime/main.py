from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes import health, sessions
from app.services.runtime import runtime_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await runtime_service.startup()
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
