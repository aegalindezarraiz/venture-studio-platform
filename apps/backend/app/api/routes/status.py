"""
/status — Dashboard en tiempo real del estado de todos los agentes.
Consulta Notion + health endpoints concurrentemente y devuelve el resumen.
"""
import asyncio
import os
import time
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Query

router = APIRouter()

NOTION_TOKEN   = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"
NOTION_BASE    = "https://api.notion.com/v1"
NOTION_DBS = {
    "startups":       os.environ.get("NOTION_DB_STARTUPS",       "460c359a4f8849bd9c9a003e7520e7c0"),
    "okrs":           os.environ.get("NOTION_DB_OKRS",           "6575a70444b7404f87f1b1161b21748a"),
    "tasks":          os.environ.get("NOTION_DB_TASKS",          "1a166396f42a806ea9e1c2512f451f28"),
    "experiments":    os.environ.get("NOTION_DB_EXPERIMENTS",    "c00a6a2cde6243e9af6c4c636b5a7d14"),
    "briefs":         os.environ.get("NOTION_DB_BRIEFS",         "7956591d7f774ad69ac0bf8faeec02ac"),
    "agents":         os.environ.get("NOTION_DB_AGENTS",         "cf83b9a4254a4140910e1bf50b3fd7d2"),
    "weekly_reviews": os.environ.get("NOTION_DB_WEEKLY_REVIEWS", "465c28a2359f449ba3865dd15df0a683"),
}

# Servicios conocidos (fallback si Notion no tiene agentes registrados aún)
_KNOWN_SERVICES = [
    {"name": "Backend",                  "url": os.environ.get("BACKEND_URL",            "http://localhost:8000"), "type": "Runtime"},
    {"name": "Agent Runtime",            "url": os.environ.get("AGENT_RUNTIME_URL",      "http://localhost:8001"), "type": "Runtime"},
    {"name": "ScaleOS Supervisor",       "url": os.environ.get("SCALEOS_SUPERVISOR_URL", "http://localhost:8002"), "type": "Supervisor"},
    {"name": "SEO & OSINT Agent",        "url": os.environ.get("SEO_OSINT_AGENT_URL",    "http://localhost:8003"), "type": "SEO/OSINT"},
    {"name": "Growth Intelligence Agent","url": os.environ.get("GROWTH_INTELLIGENCE_URL","http://localhost:8004"), "type": "Growth"},
]


def _notion_headers():
    return {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": NOTION_VERSION}


def _extract_title(page):
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", [])).strip()
    return ""


def _extract_select(page, key):
    prop = page.get("properties", {}).get(key, {})
    sel = prop.get("select")
    return sel.get("name") if sel else None


def _extract_url(page, key):
    return page.get("properties", {}).get(key, {}).get("url")


def _extract_date(page, key):
    d = page.get("properties", {}).get(key, {}).get("date")
    return d.get("start") if d else None


def _extract_number(page, key):
    return page.get("properties", {}).get(key, {}).get("number")


async def _fetch_notion_agents(client: httpx.AsyncClient) -> list[dict]:
    if not NOTION_TOKEN:
        return []
    try:
        r = await client.post(
            f"{NOTION_BASE}/databases/{NOTION_DBS['agents']}/query",
            headers=_notion_headers(),
            json={},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        return [
            {
                "name":        _extract_title(p),
                "type":        _extract_select(p, "Type"),
                "status":      _extract_select(p, "Status"),
                "model":       _extract_select(p, "Model"),
                "service_url": _extract_url(p, "Service URL"),
                "last_run":    _extract_date(p, "Last Run"),
                "runs_total":  _extract_number(p, "Runs Total") or 0,
            }
            for p in r.json().get("results", [])
        ]
    except Exception:
        return []


async def _check_health(client: httpx.AsyncClient, name: str, url: str, agent_meta: dict, timeout: float) -> dict:
    if not url:
        return {"name": name, "ready": False, "error": "no_url", "latency_ms": None, **agent_meta}

    start = time.perf_counter()
    try:
        r = await client.get(f"{url.rstrip('/')}/health", timeout=timeout)
        latency_ms = round((time.perf_counter() - start) * 1000)
        ready = r.status_code == 200
        body = {}
        try:
            body = r.json()
        except Exception:
            pass
        return {
            "name": name, "ready": ready,
            "http_status": r.status_code, "latency_ms": latency_ms,
            "health_body": body, **agent_meta,
        }
    except httpx.ConnectError:
        return {"name": name, "ready": False, "error": "connection_refused",
                "latency_ms": round((time.perf_counter() - start) * 1000), **agent_meta}
    except httpx.TimeoutException:
        return {"name": name, "ready": False, "error": f"timeout_{timeout}s",
                "latency_ms": round((time.perf_counter() - start) * 1000), **agent_meta}
    except Exception as e:
        return {"name": name, "ready": False, "error": str(e)[:120],
                "latency_ms": round((time.perf_counter() - start) * 1000), **agent_meta}


async def _check_notion_db(client: httpx.AsyncClient, db_name: str, db_id: str) -> dict:
    if not NOTION_TOKEN:
        return {"db": db_name, "accessible": False, "error": "no_token"}
    start = time.perf_counter()
    try:
        r = await client.get(f"{NOTION_BASE}/databases/{db_id}", headers=_notion_headers(), timeout=8)
        return {
            "db": db_name,
            "accessible": r.status_code == 200,
            "http_status": r.status_code,
            "latency_ms": round((time.perf_counter() - start) * 1000),
        }
    except Exception as e:
        return {"db": db_name, "accessible": False, "error": str(e)[:80],
                "latency_ms": round((time.perf_counter() - start) * 1000)}


async def _build_status(timeout: float) -> dict:
    ts_start = time.perf_counter()
    generated_at = datetime.utcnow().isoformat() + "Z"

    async with httpx.AsyncClient() as client:
        # Fetch agentes de Notion + check DBs en paralelo
        agents_task = _fetch_notion_agents(client)
        db_tasks = [_check_notion_db(client, name, db_id) for name, db_id in NOTION_DBS.items()]
        notion_agents, *db_results = await asyncio.gather(agents_task, *db_tasks)

        # Construir lista final de agentes a chequear
        if notion_agents:
            to_check = [
                (a["name"], a.get("service_url", ""), {
                    "type": a.get("type"),
                    "model": a.get("model"),
                    "notion_status": a.get("status"),
                    "last_run": a.get("last_run"),
                    "runs_total": a.get("runs_total"),
                    "source": "notion",
                })
                for a in notion_agents
            ]
        else:
            # Fallback: servicios conocidos del entorno
            to_check = [
                (s["name"], s["url"], {"type": s["type"], "source": "env"})
                for s in _KNOWN_SERVICES
            ]

        # Health checks en paralelo
        health_results = await asyncio.gather(*[
            _check_health(client, name, url, meta, timeout)
            for name, url, meta in to_check
        ])

    # Métricas de resumen
    total      = len(health_results)
    ready      = [r for r in health_results if r["ready"]]
    failed     = [r for r in health_results if not r["ready"]]
    dbs_ok     = [d for d in db_results if d.get("accessible")]
    pct_ready  = round(len(ready) / total * 100) if total else 0

    overall = "healthy" if pct_ready == 100 else "degraded" if pct_ready >= 50 else "critical"

    return {
        "generated_at":       generated_at,
        "response_time_ms":   round((time.perf_counter() - ts_start) * 1000),
        "overall":            overall,
        "summary": {
            "total_agents":   total,
            "ready":          len(ready),
            "failed":         len(failed),
            "pct_ready":      pct_ready,
            "notion_dbs_ok":  len(dbs_ok),
            "notion_dbs_total": len(db_results),
            "notion_connected": len(dbs_ok) == len(db_results),
        },
        "agents":      health_results,
        "notion_dbs":  db_results,
    }


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="Estado en tiempo real de todos los agentes",
    description=(
        "Consulta concurrentemente: Notion API (7 DBs) + health endpoint de cada agente. "
        "Devuelve resumen y detalle por agente."
    ),
)
async def get_status(timeout: float = Query(5.0, ge=0.5, le=30.0, description="Timeout por health check (segundos)")):
    return await _build_status(timeout)


@router.get("/summary", summary="Resumen compacto — solo métricas")
async def get_status_summary(timeout: float = Query(3.0, ge=0.5, le=15.0)):
    data = await _build_status(timeout)
    return {
        "generated_at":   data["generated_at"],
        "overall":        data["overall"],
        "response_time_ms": data["response_time_ms"],
        **data["summary"],
        "failed_agents": [
            {"name": a["name"], "error": a.get("error"), "type": a.get("type")}
            for a in data["agents"] if not a["ready"]
        ],
    }
