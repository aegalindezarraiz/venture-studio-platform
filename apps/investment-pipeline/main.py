"""Investment Pipeline - due diligence and portfolio analysis. Port: 8006"""
import os
from contextlib import asynccontextmanager
from typing import Optional
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Investment Pipeline - started")
    yield

app = FastAPI(title="Investment Pipeline", version="1.0.0", lifespan=lifespan)
_ai = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class DDRequest(BaseModel):
    startup_name: str
    sector: str
    stage: str
    investment_amount_usd: int
    description: str
    metrics: Optional[dict] = None

class PortfolioRequest(BaseModel):
    portfolio: list[dict]
    analysis_type: str = "health"

@app.get("/health")
async def health():
    return {"status": "ok", "service": "investment-pipeline"}

@app.post("/investments/due-diligence")
async def due_diligence(req: DDRequest):
    prompt = f"""Due diligence for investment:
Startup: {req.startup_name}, Sector: {req.sector}, Stage: {req.stage}
Investment: ${req.investment_amount_usd:,}, Description: {req.description}
Metrics: {req.metrics or "Not provided"}

Evaluate: viability score (1-10), top 5 risks, strengths, market analysis,
financial projections, deal structure recommendation, post-investment milestones,
final recommendation: INVEST / PASS / NEGOTIATE. JSON."""
    r = _ai.messages.create(model="claude-opus-4-6", max_tokens=3000,
                             messages=[{"role": "user", "content": prompt}])
    return {"startup": req.startup_name, "due_diligence": r.content[0].text}

@app.post("/investments/portfolio-analysis")
async def portfolio_analysis(req: PortfolioRequest):
    prompt = f"Analyze venture studio portfolio: {req.portfolio}. Type: {req.analysis_type}. Include: portfolio metrics, diversification, expected returns, strategic recommendations. JSON."
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=2048,
                             messages=[{"role": "user", "content": prompt}])
    return {"analysis_type": req.analysis_type, "analysis": r.content[0].text}
