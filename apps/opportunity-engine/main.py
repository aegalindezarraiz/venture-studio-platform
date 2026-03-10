"""Opportunity Engine - discover and validate business opportunities. Port: 8003"""
import os
from contextlib import asynccontextmanager
from typing import Optional
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Opportunity Engine - started")
    yield

app = FastAPI(title="Opportunity Engine", version="1.0.0", lifespan=lifespan)
_ai = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class OpportunityRequest(BaseModel):
    problem_statement: str
    target_market: str
    budget_range: Optional[str] = None
    timeline_months: int = 12

@app.get("/health")
async def health():
    return {"status": "ok", "service": "opportunity-engine"}

@app.post("/opportunities/discover")
async def discover(req: OpportunityRequest):
    prompt = f"""Discover business opportunities for:
Problem: {req.problem_statement}
Market: {req.target_market}
Budget: {req.budget_range or "Flexible"}
Timeline: {req.timeline_months} months

Generate 3 concrete opportunities with: name, description, business model, TAM estimate,
viability score (1-10), validation next steps. JSON."""
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=2048,
                             messages=[{"role": "user", "content": prompt}])
    return {"opportunities": r.content[0].text, "problem": req.problem_statement}

@app.post("/opportunities/validate")
async def validate(hypothesis: str, method: str = "mvp"):
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=1024,
                             messages=[{"role": "user", "content": f"Validation plan for: {hypothesis}. Method: {method}. Include: success metrics, experiments, go/no-go criteria. JSON."}])
    return {"validation_plan": r.content[0].text, "hypothesis": hypothesis}

@app.get("/opportunities/scoring-criteria")
async def criteria():
    return {"criteria": ["market_size", "competition", "timing", "team_fit", "technical_feasibility", "monetization"]}
