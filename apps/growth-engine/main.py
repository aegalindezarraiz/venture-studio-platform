"""Growth Engine - growth strategies and experiments. Port: 8007"""
import os
from contextlib import asynccontextmanager
from typing import Optional
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Growth Engine - started")
    yield

app = FastAPI(title="Growth Engine", version="1.0.0", lifespan=lifespan)
_ai = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class GrowthRequest(BaseModel):
    startup_name: str
    current_mrr_usd: Optional[int] = None
    target_mrr_usd: Optional[int] = None
    channels: list[str] = []
    timeline_months: int = 6
    budget_usd: Optional[int] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "growth-engine"}

@app.post("/growth/strategy")
async def growth_strategy(req: GrowthRequest):
    prompt = f"""Design growth strategy for {req.startup_name}:
MRR: ${req.current_mrr_usd or 0:,} -> ${req.target_mrr_usd or "TBD":,}
Channels: {", ".join(req.channels) or "None"}
Timeline: {req.timeline_months} months, Budget: ${req.budget_usd or "Flexible"}

Include: North Star Metric, growth loops, acquisition plan per channel (with ROI),
activation/retention plan, top 5 experiments (hypothesis + metrics), monthly OKRs, tool stack. JSON."""
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=3000,
                             messages=[{"role": "user", "content": prompt}])
    return {"startup": req.startup_name, "strategy": r.content[0].text}

@app.post("/growth/content-strategy")
async def content_strategy(startup_name: str, audience: str, channels: str, value_prop: str):
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=2048,
                             messages=[{"role": "user", "content": f"3-month content strategy for {startup_name}: audience={audience}, channels={channels}, value_prop={value_prop}. Include editorial calendar, content types, channel metrics, post templates. JSON."}])
    return {"startup": startup_name, "content_strategy": r.content[0].text}

@app.post("/growth/experiment")
async def design_experiment(hypothesis: str, metric: str, current_value: float, target_value: float):
    r = _ai.messages.create(model="claude-haiku-4-5-20251001", max_tokens=800,
                             messages=[{"role": "user", "content": f"Design A/B experiment: hypothesis={hypothesis}, metric={metric}, current={current_value}, target={target_value}. Include sample size, duration, go/no-go criteria. JSON."}])
    return {"experiment": r.content[0].text}
