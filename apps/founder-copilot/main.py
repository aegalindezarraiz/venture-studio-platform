"""Founder Copilot - personal AI for portfolio founders. Port: 8008"""
import os
from contextlib import asynccontextmanager
from typing import Optional
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

SYSTEM = """You are the Copilot of an elite venture studio. Help founders make better decisions faster.
You have deep expertise in: strategy, fundraising, hiring, product, marketing, sales, finance, crisis management.
Be direct, practical, and results-oriented."""

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Founder Copilot - started")
    yield

app = FastAPI(title="Founder Copilot", version="1.0.0", lifespan=lifespan)
_ai = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    founder_name: Optional[str] = None

class DecisionRequest(BaseModel):
    decision: str
    options: list[str]
    constraints: Optional[str] = None
    startup_context: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "founder-copilot"}

@app.post("/copilot/chat")
async def chat(req: ChatRequest):
    content = f"Startup context: {req.context}

Question: {req.message}" if req.context else req.message
    r = _ai.messages.create(model="claude-opus-4-6", max_tokens=2048, system=SYSTEM,
                             messages=[{"role": "user", "content": content}])
    return {"response": r.content[0].text, "founder": req.founder_name or "Founder", "tokens": r.usage.output_tokens}

@app.post("/copilot/decision-framework")
async def decision(req: DecisionRequest):
    opts = "
".join(f"{i+1}. {o}" for i, o in enumerate(req.options))
    prompt = f"""Decision needed:
Decision: {req.decision}
Options:
{opts}
Constraints: {req.constraints or "None"}
Context: {req.startup_context or "Not provided"}

Apply framework:
1. Clarify the real problem
2. Evaluate each option (pros/cons/risks)
3. Identify critical missing information
4. Recommendation with justification
5. Implementation plan
6. Success metrics

JSON."""
    r = _ai.messages.create(model="claude-opus-4-6", max_tokens=2500, system=SYSTEM,
                             messages=[{"role": "user", "content": prompt}])
    return {"decision": req.decision, "analysis": r.content[0].text}

@app.post("/copilot/weekly-planning")
async def weekly_plan(startup_name: str, goals: str, blockers: str = ""):
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=1500, system=SYSTEM,
                             messages=[{"role": "user", "content": f"Startup: {startup_name}
Goals: {goals}
Blockers: {blockers}

Generate prioritized weekly plan: top 3 moves, estimated time per task, specific advice. JSON."}])
    return {"startup": startup_name, "weekly_plan": r.content[0].text}
