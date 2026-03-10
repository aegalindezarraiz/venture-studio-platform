"""Writes all enterprise app files for the AI Venture Studio OS."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  {path}")

DOCKERFILE = lambda name, port: f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/{name}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/{name}/ .
COPY packages/ /packages/
ENV PYTHONPATH=/app:/packages
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:{port}/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{{{"PORT:-{port}}}}}"]
"""

REQUIREMENTS_AI = """fastapi==0.115.0
uvicorn[standard]==0.30.6
anthropic==0.34.2
httpx==0.27.0
pydantic==2.8.2
"""

REQUIREMENTS_DB = """fastapi==0.115.0
uvicorn[standard]==0.30.6
anthropic==0.34.2
httpx==0.27.0
pydantic==2.8.2
sqlalchemy==2.0.31
asyncpg==0.29.0
redis==5.0.8
"""

# ── api-gateway ───────────────────────────────────────────────────────────────
w("apps/api-gateway/requirements.txt", """fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.0
python-jose[cryptography]==3.3.0
prometheus-client==0.20.0
""")

w("apps/api-gateway/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api-gateway/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8000}}"]
""")

w("apps/api-gateway/main.py", '''"""
API Gateway - single entry point for AI Venture Studio OS.
Port: 8000
"""
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

SERVICES = {
    "auth":         os.environ.get("AUTH_SERVICE_URL",        "http://localhost:8010"),
    "backend":      os.environ.get("BACKEND_URL",             "http://localhost:8020"),
    "orchestrator": os.environ.get("AGENT_ORCHESTRATOR_URL",  "http://localhost:8001"),
    "market-intel": os.environ.get("MARKET_INTEL_URL",        "http://localhost:8002"),
    "opportunity":  os.environ.get("OPPORTUNITY_ENGINE_URL",  "http://localhost:8003"),
    "product":      os.environ.get("PRODUCT_FACTORY_URL",     "http://localhost:8004"),
    "startup":      os.environ.get("STARTUP_GENERATOR_URL",   "http://localhost:8005"),
    "investment":   os.environ.get("INVESTMENT_PIPELINE_URL", "http://localhost:8006"),
    "growth":       os.environ.get("GROWTH_ENGINE_URL",       "http://localhost:8007"),
    "copilot":      os.environ.get("FOUNDER_COPILOT_URL",     "http://localhost:8008"),
}

ROUTE_MAP = {
    "/auth":          "auth",
    "/agents":        "backend",
    "/monitor":       "backend",
    "/notion":        "backend",
    "/status":        "backend",
    "/orchestrate":   "orchestrator",
    "/intel":         "market-intel",
    "/opportunities": "opportunity",
    "/products":      "product",
    "/startups":      "startup",
    "/investments":   "investment",
    "/growth":        "growth",
    "/copilot":       "copilot",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API Gateway - started")
    yield

app = FastAPI(title="AI Venture Studio OS - API Gateway", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"service": "AI Venture Studio OS", "routes": list(ROUTE_MAP.keys()), "docs": "/docs"}

@app.get("/services/status")
async def services_status():
    results = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in SERVICES.items():
            try:
                r = await client.get(f"{url}/health")
                results[name] = {"ready": r.status_code == 200, "url": url}
            except Exception as e:
                results[name] = {"ready": False, "url": url, "error": str(e)[:60]}
    ready = sum(1 for v in results.values() if v["ready"])
    return {"total": len(results), "ready": ready, "services": results}

async def _proxy(request: Request, upstream_url: str) -> JSONResponse:
    path = request.url.path
    query = request.url.query
    target = f"{upstream_url.rstrip(\'/\')}{path}"
    if query:
        target = f"{target}?{query}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.request(method=request.method, url=target, headers=headers, content=body)
    try:
        data = r.json()
    except Exception:
        data = {"body": r.text}
    return JSONResponse(content=data, status_code=r.status_code)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def gateway(path: str, request: Request):
    prefix = "/" + path.split("/")[0]
    service_key = ROUTE_MAP.get(prefix)
    if not service_key:
        raise HTTPException(status_code=404, detail=f"No route for /{path}")
    return await _proxy(request, SERVICES[service_key])
''')

# ── agent-orchestrator ────────────────────────────────────────────────────────
w("apps/agent-orchestrator/requirements.txt", """fastapi==0.115.0
uvicorn[standard]==0.30.6
anthropic==0.34.2
httpx==0.27.0
redis==5.0.8
pydantic==2.8.2
""")

w("apps/agent-orchestrator/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/agent-orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/agent-orchestrator/ .
COPY packages/ /packages/
ENV PYTHONPATH=/app:/packages
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8001/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8001}}"]
""")

w("apps/agent-orchestrator/main.py", '''"""Agent Orchestrator - coordinates agent execution. Port: 8001"""
import json, os, uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Agent Orchestrator - started")
    yield

app = FastAPI(title="Agent Orchestrator", version="1.0.0", lifespan=lifespan)

class TaskRequest(BaseModel):
    agent_id: str
    task_type: str
    payload: dict
    priority: int = 2
    callback_url: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-orchestrator"}

@app.post("/orchestrate/run")
async def run_task(req: TaskRequest):
    task_id = str(uuid.uuid4())
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        task = {"id": task_id, "status": "queued", "created_at": datetime.now(timezone.utc).isoformat(), **req.dict()}
        r.setex(f"task:{task_id}", 86400, json.dumps(task))
        r.lpush("task_queue", task_id)
        r.close()
    except Exception as e:
        pass
    return {"task_id": task_id, "status": "queued", "agent_id": req.agent_id}

@app.get("/orchestrate/tasks/{task_id}")
async def task_status(task_id: str):
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        data = r.get(f"task:{task_id}")
        r.close()
        if data:
            return json.loads(data)
    except Exception:
        pass
    return {"task_id": task_id, "status": "not_found"}

@app.get("/orchestrate/queue/stats")
async def queue_stats():
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        depth = r.llen("task_queue")
        r.close()
        return {"queued_tasks": depth}
    except Exception as e:
        return {"queued_tasks": 0, "error": str(e)}
''')

# ── market-intel ──────────────────────────────────────────────────────────────
w("apps/market-intel/requirements.txt", REQUIREMENTS_AI)
w("apps/market-intel/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/market-intel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/market-intel/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8002/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8002}}"]
""")

w("apps/market-intel/main.py", '''"""Market Intelligence - market analysis and competitive signals. Port: 8002"""
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
''')

# ── opportunity-engine ─────────────────────────────────────────────────────────
w("apps/opportunity-engine/requirements.txt", REQUIREMENTS_AI)
w("apps/opportunity-engine/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/opportunity-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/opportunity-engine/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8003/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8003}}"]
""")

w("apps/opportunity-engine/main.py", '''"""Opportunity Engine - discover and validate business opportunities. Port: 8003"""
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
''')

# ── product-factory ───────────────────────────────────────────────────────────
w("apps/product-factory/requirements.txt", REQUIREMENTS_AI)
w("apps/product-factory/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/product-factory/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/product-factory/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8004/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8004}}"]
""")

w("apps/product-factory/main.py", '''"""Product Factory - PRDs, roadmaps, user stories. Port: 8004"""
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
''')

# ── startup-generator ─────────────────────────────────────────────────────────
w("apps/startup-generator/requirements.txt", REQUIREMENTS_AI)
w("apps/startup-generator/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/startup-generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/startup-generator/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8005/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8005}}"]
""")

w("apps/startup-generator/main.py", '''"""Startup Generator - generate and validate startup concepts. Port: 8005"""
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
''')

# ── investment-pipeline ────────────────────────────────────────────────────────
w("apps/investment-pipeline/requirements.txt", REQUIREMENTS_DB)
w("apps/investment-pipeline/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/investment-pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/investment-pipeline/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8006/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8006}}"]
""")

w("apps/investment-pipeline/main.py", '''"""Investment Pipeline - due diligence and portfolio analysis. Port: 8006"""
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
''')

# ── growth-engine ─────────────────────────────────────────────────────────────
w("apps/growth-engine/requirements.txt", REQUIREMENTS_AI)
w("apps/growth-engine/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/growth-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/growth-engine/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8007/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8007}}"]
""")

w("apps/growth-engine/main.py", '''"""Growth Engine - growth strategies and experiments. Port: 8007"""
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
''')

# ── founder-copilot ────────────────────────────────────────────────────────────
w("apps/founder-copilot/requirements.txt", REQUIREMENTS_AI + "redis==5.0.8\n")
w("apps/founder-copilot/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/founder-copilot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/founder-copilot/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8008/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8008}}"]
""")

w("apps/founder-copilot/main.py", '''"""Founder Copilot - personal AI for portfolio founders. Port: 8008"""
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
    content = f"Startup context: {req.context}\n\nQuestion: {req.message}" if req.context else req.message
    r = _ai.messages.create(model="claude-opus-4-6", max_tokens=2048, system=SYSTEM,
                             messages=[{"role": "user", "content": content}])
    return {"response": r.content[0].text, "founder": req.founder_name or "Founder", "tokens": r.usage.output_tokens}

@app.post("/copilot/decision-framework")
async def decision(req: DecisionRequest):
    opts = "\n".join(f"{i+1}. {o}" for i, o in enumerate(req.options))
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
                             messages=[{"role": "user", "content": f"Startup: {startup_name}\nGoals: {goals}\nBlockers: {blockers}\n\nGenerate prioritized weekly plan: top 3 moves, estimated time per task, specific advice. JSON."}])
    return {"startup": startup_name, "weekly_plan": r.content[0].text}
''')

# ── auth-service ──────────────────────────────────────────────────────────────
w("apps/auth-service/requirements.txt", """fastapi==0.115.0
uvicorn[standard]==0.30.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.8.2
sqlalchemy==2.0.31
asyncpg==0.29.0
""")

w("apps/auth-service/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/auth-service/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8010/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8010}}"]
""")

w("apps/auth-service/main.py", '''"""Auth Service - JWT authentication and authorization. Port: 8010"""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-use-32-char-min")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Auth Service - started")
    yield

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    org_id: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service"}

@app.post("/auth/token", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    from jose import jwt
    payload = {
        "sub": form.username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
        "roles": ["founder"],
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "expires_in": EXPIRE_MINUTES * 60}

@app.post("/auth/register")
async def register(user: UserCreate):
    return {"status": "created", "email": user.email, "message": "Check your email for verification."}

@app.post("/auth/verify")
async def verify(token: str = Depends(oauth2)):
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "sub": payload.get("sub"), "roles": payload.get("roles", [])}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.post("/auth/refresh")
async def refresh(token: str = Depends(oauth2)):
    from jose import jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
        return {"access_token": jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
''')

# ── org-service ────────────────────────────────────────────────────────────────
w("apps/org-service/requirements.txt", """fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.8.2
sqlalchemy==2.0.31
asyncpg==0.29.0
""")

w("apps/org-service/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/org-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/org-service/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8011/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8011}}"]
""")

w("apps/org-service/main.py", '''"""Org Service - organizations, teams, and permissions. Port: 8011"""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Org Service - started")
    yield

app = FastAPI(title="Org Service", version="1.0.0", lifespan=lifespan)

class OrgCreate(BaseModel):
    name: str
    slug: str
    plan: str = "starter"

class MemberInvite(BaseModel):
    email: str
    role: str = "member"

@app.get("/health")
async def health():
    return {"status": "ok", "service": "org-service"}

@app.post("/organizations")
async def create_org(org: OrgCreate):
    return {"status": "created", "id": f"org_{org.slug}", **org.dict()}

@app.get("/organizations/{org_id}")
async def get_org(org_id: str):
    return {"id": org_id, "name": "Demo Org", "plan": "growth", "members": 5}

@app.post("/organizations/{org_id}/members")
async def invite_member(org_id: str, invite: MemberInvite):
    return {"status": "invited", **invite.dict(), "org_id": org_id}

@app.get("/organizations/{org_id}/members")
async def list_members(org_id: str):
    return {"org_id": org_id, "members": []}
''')

# ── billing-service ────────────────────────────────────────────────────────────
w("apps/billing-service/requirements.txt", """fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.8.2
sqlalchemy==2.0.31
asyncpg==0.29.0
""")

w("apps/billing-service/Dockerfile", f"""FROM python:3.11-slim
WORKDIR /app
COPY apps/billing-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/billing-service/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8012/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${{PORT:-8012}}"]
""")

w("apps/billing-service/main.py", '''"""Billing Service - subscriptions and payments. Port: 8012"""
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

PLANS = {
    "starter":    {"price_usd": 299,  "agents": 50,  "startups": 3},
    "growth":     {"price_usd": 799,  "agents": 200, "startups": 10},
    "enterprise": {"price_usd": 2499, "agents": 500, "startups": -1},
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Billing Service - started")
    yield

app = FastAPI(title="Billing Service", version="1.0.0", lifespan=lifespan)

class SubscriptionCreate(BaseModel):
    org_id: str
    plan: str
    payment_method_id: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "billing-service"}

@app.get("/billing/plans")
async def list_plans():
    return {"plans": PLANS}

@app.post("/billing/subscriptions")
async def create_subscription(req: SubscriptionCreate):
    if req.plan not in PLANS:
        raise HTTPException(400, f"Invalid plan. Options: {list(PLANS.keys())}")
    return {"status": "created", "org_id": req.org_id, "plan": req.plan, **PLANS[req.plan]}

@app.get("/billing/subscriptions/{org_id}")
async def get_subscription(org_id: str):
    return {"org_id": org_id, "plan": "growth", "status": "active", "next_billing": "2026-04-10"}

@app.delete("/billing/subscriptions/{org_id}")
async def cancel(org_id: str):
    return {"status": "cancelled", "org_id": org_id, "effective_date": "end_of_period"}
''')

# ── packages/agent-sdk ─────────────────────────────────────────────────────────
w("packages/agent-sdk/__init__.py", '''"""Agent SDK - base classes and types for AI Venture Studio OS agents."""
from packages.agent_sdk.types import AgentContext, AgentResult, AgentStatus
from packages.agent_sdk.base_agent import BaseAgent
from packages.agent_sdk.decorators import agent, tool

__all__ = ["BaseAgent", "AgentContext", "AgentResult", "AgentStatus", "agent", "tool"]
''')

w("packages/agent-sdk/types.py", '''"""Core types for the Agent SDK."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class AgentStatus(str, Enum):
    IDLE    = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR   = "error"
    TIMEOUT = "timeout"

@dataclass
class AgentContext:
    task_id:    str
    agent_id:   str
    org_id:     Optional[str]      = None
    startup_id: Optional[str]      = None
    payload:    dict[str, Any]     = field(default_factory=dict)
    memory:     dict[str, Any]     = field(default_factory=dict)
    metadata:   dict[str, Any]     = field(default_factory=dict)
    created_at: datetime           = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class AgentResult:
    task_id:      str
    agent_id:     str
    status:       AgentStatus
    output:       Any               = None
    error:        Optional[str]     = None
    duration_ms:  Optional[int]     = None
    tokens_used:  Optional[int]     = None
    metadata:     dict[str, Any]    = field(default_factory=dict)
    completed_at: datetime          = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "agent_id": self.agent_id,
            "status": self.status.value, "output": self.output, "error": self.error,
            "duration_ms": self.duration_ms, "tokens_used": self.tokens_used,
            "metadata": self.metadata, "completed_at": self.completed_at.isoformat(),
        }
''')

w("packages/agent-sdk/base_agent.py", '''"""BaseAgent - base class for all Venture Studio AI agents."""
import abc, logging, os, time
from typing import Any, Optional
import anthropic
from packages.agent_sdk.types import AgentContext, AgentResult, AgentStatus

class BaseAgent(abc.ABC):
    agent_id:     str = "base-agent"
    agent_name:   str = "Base Agent"
    model:        str = "claude-sonnet-4-6"
    max_tokens:   int = 2048
    system_prompt: str = "You are a specialized AI agent of the AI Venture Studio OS."

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        self.log = logging.getLogger(f"agent.{self.agent_id}")

    @abc.abstractmethod
    async def execute(self, ctx: AgentContext) -> AgentResult: ...

    async def run(self, ctx: AgentContext) -> AgentResult:
        start = time.perf_counter()
        self.log.info(f"[{ctx.task_id}] Starting")
        try:
            result = await self.execute(ctx)
            result.duration_ms = round((time.perf_counter() - start) * 1000)
            self.log.info(f"[{ctx.task_id}] Done in {result.duration_ms}ms")
            return result
        except Exception as e:
            ms = round((time.perf_counter() - start) * 1000)
            self.log.error(f"[{ctx.task_id}] Error: {e}")
            return AgentResult(task_id=ctx.task_id, agent_id=self.agent_id,
                               status=AgentStatus.ERROR, error=str(e), duration_ms=ms)

    def call_llm(self, prompt: str, system: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        r = self._client.messages.create(
            model=self.model, max_tokens=max_tokens or self.max_tokens,
            system=system or self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text
''')

w("packages/agent-sdk/decorators.py", '''"""Decorators for the Agent SDK."""
import functools, logging
from typing import Callable

def agent(agent_id: str, name: str, category: str, priority: int = 2):
    def decorator(func: Callable):
        func._agent_id = agent_id
        func._agent_name = name
        func._agent_category = category
        func._agent_priority = priority
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def tool(name: str, description: str):
    def decorator(func: Callable):
        func._tool_name = name
        func._tool_description = description
        func._is_tool = True
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
''')

# ── packages/prompt-registry ──────────────────────────────────────────────────
w("packages/prompt-registry/__init__.py", '''"""Prompt Registry - centralized prompt storage for AI Venture Studio OS."""
from packages.prompt_registry.registry import PromptRegistry, get_prompt, register_prompt
__all__ = ["PromptRegistry", "get_prompt", "register_prompt"]
''')

w("packages/prompt-registry/registry.py", '''"""Centralized prompt registry with versioning and org overrides."""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PromptTemplate:
    id: str
    name: str
    template: str
    category: str
    version: int = 1
    variables: list[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        result = self.template
        for k, v in kwargs.items():
            result = result.replace(f"{{{k}}}", str(v))
        return result

_registry: dict[str, PromptTemplate] = {}

def register_prompt(p: PromptTemplate) -> None:
    _registry[p.id] = p

def get_prompt(prompt_id: str, org_id: Optional[str] = None) -> Optional[PromptTemplate]:
    if org_id and f"{org_id}:{prompt_id}" in _registry:
        return _registry[f"{org_id}:{prompt_id}"]
    return _registry.get(prompt_id)

class PromptRegistry:
    def __init__(self, org_id: Optional[str] = None):
        self.org_id = org_id

    def get(self, prompt_id: str, **kwargs) -> str:
        p = get_prompt(prompt_id, self.org_id)
        if not p:
            raise KeyError(f"Prompt \'{prompt_id}\' not found")
        return p.render(**kwargs) if kwargs else p.template

    def register(self, p: PromptTemplate) -> None:
        register_prompt(p)

    def list(self, category: Optional[str] = None) -> list[PromptTemplate]:
        items = list(_registry.values())
        return [i for i in items if i.category == category] if category else items

# Pre-load system prompts
for _p in [
    PromptTemplate("market_analysis", "Market Analysis", "Analyze {sector} market for {target_market}. TAM/SAM/SOM, trends, opportunities. JSON.", "intel", variables=["sector", "target_market"]),
    PromptTemplate("startup_brief", "Startup Brief", "Executive brief for {startup_name} in {sector}. Problem: {problem}. Solution: {solution}. Markdown.", "product", variables=["startup_name", "sector", "problem", "solution"]),
    PromptTemplate("okr_generator", "OKR Generator", "Generate OKRs for Q{quarter} {year} for {startup_name}. Focus: {focus_area}. 3 objectives x 3 KRs. JSON.", "executive", variables=["quarter", "year", "startup_name", "focus_area"]),
    PromptTemplate("due_diligence", "Due Diligence", "Due diligence for {startup_name} ({sector}, {stage}). Investment: ${investment_usd}. {description}. INVEST/PASS/NEGOTIATE. JSON.", "investment", variables=["startup_name", "sector", "stage", "investment_usd", "description"]),
]:
    register_prompt(_p)
''')

# ── packages/memory-engine ────────────────────────────────────────────────────
w("packages/memory-engine/__init__.py", '''"""Memory Engine - semantic memory with Qdrant + Redis."""
from packages.memory_engine.engine import MemoryEngine
__all__ = ["MemoryEngine"]
''')

w("packages/memory-engine/engine.py", '''"""Memory Engine - short-term (Redis) and long-term (Qdrant) memory for agents."""
import json, logging, os
from typing import Any, Optional

log = logging.getLogger("memory-engine")
REDIS_URL  = os.environ.get("REDIS_URL",  "redis://localhost:6379/0")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "venture_memory")

class MemoryEngine:
    def __init__(self, agent_id: str, org_id: Optional[str] = None):
        self.agent_id = agent_id
        self.org_id   = org_id
        self._redis   = None

    def _r(self):
        if not self._redis:
            import redis
            self._redis = redis.from_url(REDIS_URL, decode_responses=True)
        return self._redis

    def _ns(self, key: str) -> str:
        prefix = f"{self.org_id}:{self.agent_id}" if self.org_id else self.agent_id
        return f"mem:{prefix}:{key}"

    def remember(self, key: str, value: Any, ttl: int = 3600) -> None:
        try:
            self._r().setex(self._ns(key), ttl, json.dumps(value))
        except Exception as e:
            log.warning(f"remember error ({key}): {e}")

    def recall(self, key: str) -> Optional[Any]:
        try:
            data = self._r().get(self._ns(key))
            return json.loads(data) if data else None
        except Exception as e:
            log.warning(f"recall error ({key}): {e}")
            return None

    def forget(self, key: str) -> None:
        try:
            self._r().delete(self._ns(key))
        except Exception:
            pass

    def search_semantic(self, query: str, limit: int = 5) -> list[dict]:
        # TODO: implement with Qdrant + embeddings
        return []
''')

# ── packages/task-runtime ─────────────────────────────────────────────────────
w("packages/task-runtime/__init__.py", '''"""Task Runtime - async task execution with Redis."""
from packages.task_runtime.runtime import TaskRuntime, Task, TaskStatus
__all__ = ["TaskRuntime", "Task", "TaskStatus"]
''')

w("packages/task-runtime/runtime.py", '''"""Task Runtime - Redis-backed async task queue."""
import json, logging, os, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

log = logging.getLogger("task-runtime")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

class TaskStatus(str, Enum):
    PENDING   = "pending"
    QUEUED    = "queued"
    RUNNING   = "running"
    SUCCESS   = "success"
    FAILED    = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id:       str             = field(default_factory=lambda: str(uuid.uuid4()))
    type:     str             = ""
    payload:  dict[str, Any]  = field(default_factory=dict)
    status:   TaskStatus      = TaskStatus.PENDING
    result:   Optional[Any]   = None
    error:    Optional[str]   = None
    priority: int             = 2
    retries:  int             = 0

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "payload": self.payload,
                "status": self.status.value, "result": self.result, "error": self.error,
                "priority": self.priority, "retries": self.retries}

class TaskRuntime:
    def __init__(self, queue: str = "venture:tasks"):
        self.queue = queue
        self._handlers: dict[str, Callable] = {}

    def _r(self):
        import redis
        return redis.from_url(REDIS_URL, decode_responses=True)

    def register(self, task_type: str):
        def decorator(func):
            self._handlers[task_type] = func
            return func
        return decorator

    def submit(self, task: Task) -> str:
        task.status = TaskStatus.QUEUED
        r = self._r()
        r.setex(f"task:{task.id}", 86400, json.dumps(task.to_dict()))
        r.lpush(self.queue, task.id)
        r.close()
        return task.id

    def get_status(self, task_id: str) -> Optional[dict]:
        try:
            r = self._r()
            data = r.get(f"task:{task_id}")
            r.close()
            return json.loads(data) if data else None
        except Exception:
            return None

    def queue_depth(self) -> int:
        try:
            r = self._r()
            depth = r.llen(self.queue)
            r.close()
            return depth
        except Exception:
            return -1
''')

print("\nAll enterprise app files written successfully!")
print("\nSummary:")
apps = ["api-gateway", "agent-orchestrator", "market-intel", "opportunity-engine",
        "product-factory", "startup-generator", "investment-pipeline", "growth-engine",
        "founder-copilot", "auth-service", "org-service", "billing-service"]
for a in apps:
    print(f"  apps/{a}/  (main.py + Dockerfile + requirements.txt)")
packages = ["agent-sdk", "prompt-registry", "memory-engine", "task-runtime"]
for p in packages:
    print(f"  packages/{p}/  (__init__.py + core files)")
