"""Startup Generator - generate and validate startup concepts. Port: 8005"""
import os
from contextlib import asynccontextmanager
from typing import Optional
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup Generator - started")
    yield

app = FastAPI(title="Startup Generator", version="1.0.0", lifespan=lifespan)
_ai = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class StartupRequest(BaseModel):
    sector: str
    problem: str
    target_market: str
    innovation_type: str = "product"
    budget_usd: Optional[int] = None

class PitchDeckRequest(BaseModel):
    startup_name: str
    one_liner: str
    problem: str
    solution: str
    market_size: str
    business_model: str
    traction: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "startup-generator"}

@app.post("/startups/generate")
async def generate(req: StartupRequest):
    prompt = f"""Generate a complete startup concept:
Sector: {req.sector}, Problem: {req.problem}, Market: {req.target_market}
Innovation: {req.innovation_type}, Budget: ${req.budget_usd:,} if req.budget_usd else Flexible

Include: name, tagline, value proposition, business model, tech stack, 90-day MVP,
KPIs, go-to-market, founding team roles, risks, Y1 financial projection. JSON."""
    r = _ai.messages.create(model="claude-opus-4-6", max_tokens=4000,
                             messages=[{"role": "user", "content": prompt}])
    return {"startup_concept": r.content[0].text, "sector": req.sector}

@app.post("/startups/pitch-deck")
async def pitch_deck(req: PitchDeckRequest):
    prompt = f"""Generate 10-slide pitch deck content for {req.startup_name}:
One-liner: {req.one_liner}, Problem: {req.problem}, Solution: {req.solution}
Market: {req.market_size}, Model: {req.business_model}, Traction: {req.traction or "Pre-launch"}
Per slide: title, key bullets, main message. JSON."""
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=3000,
                             messages=[{"role": "user", "content": prompt}])
    return {"startup": req.startup_name, "pitch_deck": r.content[0].text}

@app.post("/startups/name-generator")
async def names(sector: str, keywords: str, count: int = 10):
    r = _ai.messages.create(model="claude-haiku-4-5-20251001", max_tokens=512,
                             messages=[{"role": "user", "content": f"Generate {count} startup names for {sector} with keywords: {keywords}. Include .com/.io/.ai domain availability estimate. JSON array."}])
    return {"names": r.content[0].text}
