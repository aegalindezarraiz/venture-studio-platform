"""SEO & OSINT Agent — punto de entrada."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import health, opportunities


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.services.notion_sync import register_self
        notion_id = register_self()
        if notion_id:
            print(f"[seo_osint_agent] Registrado en Notion: {notion_id}")
    except Exception as e:
        print(f"[seo_osint_agent] Notion registro omitido: {e}")
    yield


app = FastAPI(
    title="SEO & OSINT Agent",
    description="Inteligencia competitiva y oportunidades SEO con sincronización a Notion",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
