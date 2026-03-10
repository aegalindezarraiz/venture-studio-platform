"""
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
    target = f"{upstream_url.rstrip('/')}{path}"
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
