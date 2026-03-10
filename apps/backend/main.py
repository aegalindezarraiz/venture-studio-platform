"""
Punto de entrada del backend — AI Venture Studio OS.
Ejecutar: uvicorn main:app --host 0.0.0.0 --port 8000
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Notion (opcional: solo se inicializa si hay token)
try:
    from notion_client import Client as NotionClient
    _notion_token = os.environ.get("NOTION_TOKEN")
    notion = NotionClient(auth=_notion_token) if _notion_token else None
except ImportError:
    notion = None

# Sentry (opcional)
try:
    import sentry_sdk
    _sentry_dsn = os.environ.get("SENTRY_DSN")
    if _sentry_dsn:
        sentry_sdk.init(dsn=_sentry_dsn, traces_sample_rate=0.2)
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("AI Venture Studio OS — backend iniciado")
    yield
    # Shutdown
    print("AI Venture Studio OS — backend detenido")


app = FastAPI(
    title="AI Venture Studio OS",
    description="Backend principal: auth, multi-tenant, CRUD, agentes, workflows, memoria.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — en Railway el frontend tiene su propia URL
_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "notion": notion is not None,
    }


@app.get("/", tags=["health"])
async def root():
    return {"message": "AI Venture Studio OS API — visita /docs"}


# ── Notion: tareas ────────────────────────────────────────────────────────────
NOTION_DATABASE_ID = os.environ.get(
    "NOTION_DATABASE_ID", "1a166396f42a806ea9e1c2512f451f28"
)


@app.get("/tasks", tags=["notion"])
async def get_tasks():
    """Consulta la base de datos de Notion y devuelve los nombres de las tareas."""
    if notion is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Notion no configurado. Añade NOTION_TOKEN en las variables de entorno.",
        )

    response = notion.databases.query(database_id=NOTION_DATABASE_ID)

    tasks = []
    for page in response.get("results", []):
        properties = page.get("properties", {})
        # Busca la propiedad de tipo title (puede llamarse 'Name', 'Nombre', 'Tarea', etc.)
        for prop in properties.values():
            if prop.get("type") == "title":
                title_parts = prop.get("title", [])
                name = "".join(t.get("plain_text", "") for t in title_parts).strip()
                if name:
                    tasks.append(name)
                break

    return {"total": len(tasks), "tasks": tasks}


# ── Rutas principales ─────────────────────────────────────────────────────────
# Se importan aquí para que los errores de configuración sean visibles al arrancar
try:
    from app.api.routes import auth, organizations, startups, agents, prompts, workflows, memory

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
    app.include_router(startups.router, prefix="/startups", tags=["startups"])
    app.include_router(agents.router, prefix="/agents", tags=["agents"])
    app.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
    app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
    app.include_router(memory.router, prefix="/memory", tags=["memory"])
except ImportError as e:
    # Modo mínimo: solo health disponible hasta que se implementen las rutas
    import warnings
    warnings.warn(f"Rutas no cargadas (modo mínimo): {e}")
