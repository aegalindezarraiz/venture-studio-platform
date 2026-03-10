from fastapi import FastAPI
from app.routes import health, briefs

app = FastAPI(
    title="Growth Intelligence Agent",
    description="Genera briefs de crecimiento accionables para startups",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(briefs.router, prefix="/briefs", tags=["briefs"])
