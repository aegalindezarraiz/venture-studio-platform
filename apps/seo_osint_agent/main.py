from fastapi import FastAPI
from app.routes import health, opportunities

app = FastAPI(
    title="SEO & OSINT Agent",
    description="Agente de inteligencia competitiva y oportunidades SEO",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
