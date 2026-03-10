"""Market Intelligence - market analysis and competitive signals. Port: 8002"""
import os
from contextlib import asynccontextmanager
from typing import Optional
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Market Intel - started")
    yield

app = FastAPI(title="Market Intelligence", version="1.0.0", lifespan=lifespan)
_ai = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class MarketAnalysisRequest(BaseModel):
    sector: str
    keywords: list[str]
    depth: str = "standard"
    competitors: list[str] = []

@app.get("/health")
async def health():
    return {"status": "ok", "service": "market-intel"}

@app.post("/intel/analyze")
async def analyze_market(req: MarketAnalysisRequest):
    prompt = f"""Market analysis for:
- Sector: {req.sector}
- Keywords: {", ".join(req.keywords)}
- Competitors: {", ".join(req.competitors) if req.competitors else "Not specified"}
- Depth: {req.depth}

Provide: TAM/SAM/SOM, top 5 trends, competitive analysis, entry opportunities, key risks, timing recommendation.
JSON format."""
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=2048,
                             messages=[{"role": "user", "content": prompt}])
    return {"sector": req.sector, "analysis": r.content[0].text, "tokens": r.usage.output_tokens}

@app.post("/intel/competitor-signal")
async def competitor_signal(company: str, signal_type: str, context: str = ""):
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=1024,
                             messages=[{"role": "user", "content": f"Analyze competitive signal: Company={company}, Type={signal_type}, Context={context}. Strategic impact for venture studio. JSON."}])
    return {"company": company, "signal_type": signal_type, "analysis": r.content[0].text}

@app.get("/intel/trends/{sector}")
async def get_trends(sector: str):
    r = _ai.messages.create(model="claude-haiku-4-5-20251001", max_tokens=512,
                             messages=[{"role": "user", "content": f"Top 5 trends in {sector} for startups 2025-2026. JSON array."}])
    return {"sector": sector, "trends": r.content[0].text}
