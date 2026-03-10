"""Product Factory - PRDs, roadmaps, user stories. Port: 8004"""
import os
from contextlib import asynccontextmanager
from typing import Optional
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Product Factory - started")
    yield

app = FastAPI(title="Product Factory", version="1.0.0", lifespan=lifespan)
_ai = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class PRDRequest(BaseModel):
    product_name: str
    problem: str
    target_user: str
    key_features: list[str]
    constraints: Optional[str] = None

class RoadmapRequest(BaseModel):
    product_name: str
    current_stage: str
    timeline_quarters: int = 4
    team_size: int = 5

@app.get("/health")
async def health():
    return {"status": "ok", "service": "product-factory"}

@app.post("/products/prd")
async def generate_prd(req: PRDRequest):
    prompt = f"""Generate a professional PRD for:
Product: {req.product_name}
Problem: {req.problem}
Target user: {req.target_user}
Key features: {", ".join(req.key_features)}
Constraints: {req.constraints or "None"}

Include: executive summary, objectives, user stories, acceptance criteria, success metrics,
out-of-scope, estimated timeline. Professional Markdown format."""
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=3000,
                             messages=[{"role": "user", "content": prompt}])
    return {"product": req.product_name, "prd": r.content[0].text}

@app.post("/products/roadmap")
async def generate_roadmap(req: RoadmapRequest):
    prompt = f"""Create a {req.timeline_quarters}-quarter product roadmap:
Product: {req.product_name}, Stage: {req.current_stage}, Team: {req.team_size} people
Per quarter: objectives, features to launch, target metrics, dependencies. JSON."""
    r = _ai.messages.create(model="claude-sonnet-4-6", max_tokens=2048,
                             messages=[{"role": "user", "content": prompt}])
    return {"product": req.product_name, "roadmap": r.content[0].text}

@app.post("/products/user-stories")
async def user_stories(feature: str, context: str = ""):
    r = _ai.messages.create(model="claude-haiku-4-5-20251001", max_tokens=1024,
                             messages=[{"role": "user", "content": f"Generate 5 Gherkin user stories for: {feature}. Context: {context}"}])
    return {"feature": feature, "stories": r.content[0].text}
