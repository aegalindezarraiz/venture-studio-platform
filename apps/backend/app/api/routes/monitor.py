"""
/monitor — Panel de control del Monitor de Agentes.

Endpoints:
  POST /monitor/seed              → Registra los 500 agentes en Notion (async-friendly)
  GET  /monitor/overview          → Resumen de estados desde Notion
  POST /monitor/agents/{name}/report → Actualiza estado de un agente concreto
  POST /monitor/sync-health       → Corre health checks y actualiza el monitor en Notion
"""
import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


# ── Modelos ───────────────────────────────────────────────────────────────────

class ReportPayload(BaseModel):
    category:      str
    model:         str
    priority:      int = 2
    estado:        Literal["Online", "Trabajando", "Error"] = "Online"
    ultima_accion: str = ""
    latencia_ms:   Optional[int] = None
    runs_total:    Optional[int] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_monitor_service():
    try:
        from app.services.monitor_service import (
            seed_monitor, report_status, get_monitor_overview
        )
        return seed_monitor, report_status, get_monitor_overview
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"monitor_service no disponible: {e}")


def _seed_bg(batch_size: int):
    """Función para correr seed en background."""
    import logging
    log = logging.getLogger("monitor-seed")
    try:
        from app.services.monitor_service import seed_monitor
        result = seed_monitor(batch_size=batch_size)
        log.info(f"Monitor seed completado: {result}")
    except Exception as e:
        log.error(f"Error en monitor seed: {e}")


async def _check_and_report(client: httpx.AsyncClient, agent_name: str, agent_url: str,
                             category: str, model: str, priority: int, timeout: float):
    """Health check de un agente + reporte inmediato al Monitor de Agentes."""
    from app.services.monitor_service import report_status

    start = time.perf_counter()
    estado = "Online"
    ultima_accion = "Health check OK"
    latency_ms = None

    try:
        r = await client.get(f"{agent_url.rstrip('/')}/health", timeout=timeout)
        latency_ms = round((time.perf_counter() - start) * 1000)
        if r.status_code == 200:
            estado = "Online"
            ultima_accion = f"Health check OK ({latency_ms} ms)"
        else:
            estado = "Error"
            ultima_accion = f"HTTP {r.status_code}"
    except httpx.ConnectError:
        latency_ms = round((time.perf_counter() - start) * 1000)
        estado = "Error"
        ultima_accion = "connection_refused"
    except httpx.TimeoutException:
        latency_ms = round((time.perf_counter() - start) * 1000)
        estado = "Error"
        ultima_accion = f"timeout ({timeout}s)"
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000)
        estado = "Error"
        ultima_accion = str(e)[:200]

    # Actualizar Notion en hilo separado (blocking I/O)
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: report_status(
                name=agent_name,
                category=category,
                model=model,
                priority=priority,
                estado=estado,
                ultima_accion=ultima_accion,
                latencia_ms=latency_ms,
            )
        )
    except Exception as e:
        pass  # No romper el flujo si Notion falla

    return {
        "name": agent_name,
        "estado": estado,
        "latency_ms": latency_ms,
        "ultima_accion": ultima_accion,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/seed",
    summary="Registrar 500 agentes en el Monitor de Agentes",
    description=(
        "Crea o actualiza las 500 entradas en la DB '🤖 Monitor de Agentes' de Notion. "
        "Con run_in_background=true retorna inmediatamente y el seed corre en segundo plano."
    ),
)
async def seed_monitor_endpoint(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(10, ge=1, le=50),
    run_in_background: bool = Query(True, description="Ejecutar en background (recomendado para 500 agentes)"),
):
    _get_monitor_service()  # valida que el servicio está disponible

    if run_in_background:
        background_tasks.add_task(_seed_bg, batch_size)
        return {
            "status": "started",
            "message": f"Seed de 500 agentes lanzado en background (batch_size={batch_size}). "
                       "Revisa Notion en ~3-5 minutos.",
            "notion_url": f"https://www.notion.so/1ba923066cec454fbc9320995cfbaf7c",
        }

    from app.services.monitor_service import seed_monitor
    result = seed_monitor(batch_size=batch_size)
    return {"status": "done", **result}


@router.get(
    "/overview",
    summary="Resumen del Monitor de Agentes",
    description="Consulta la DB de Notion y devuelve conteos por estado y categoría.",
)
async def monitor_overview():
    _, _, get_monitor_overview = _get_monitor_service()
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_monitor_overview)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/agents/{agent_name}/report",
    summary="Reportar estado de un agente",
    description="Actualiza el estado de un agente concreto en el Monitor de Agentes de Notion.",
)
async def report_agent_status(agent_name: str, payload: ReportPayload):
    _, report_status, _ = _get_monitor_service()
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: report_status(
                name=agent_name,
                category=payload.category,
                model=payload.model,
                priority=payload.priority,
                estado=payload.estado,
                ultima_accion=payload.ultima_accion,
                latencia_ms=payload.latencia_ms,
                runs_total=payload.runs_total,
            )
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/sync-health",
    summary="Health check masivo + actualización del Monitor",
    description=(
        "Corre health checks en paralelo sobre los agentes registrados en Notion "
        "y actualiza su estado en el Monitor de Agentes en tiempo real."
    ),
)
async def sync_health(
    timeout: float = Query(5.0, ge=0.5, le=30.0),
):
    """
    1. Lee los agentes de la DB 🤖 Agents (fuente de verdad de URLs de servicios)
    2. Por cada agente con service_url, corre /health y actualiza el Monitor
    3. Para los agentes sin URL (catálogo teórico), los marca como 'Online' con acción 'Registered'
    """
    from packages.agents.definitions import ALL_AGENTS
    from app.services.monitor_service import report_status

    NOTION_TOKEN   = os.environ.get("NOTION_TOKEN", "")
    NOTION_BASE    = "https://api.notion.com/v1"
    NOTION_DB_AGENTS = os.environ.get("NOTION_DB_AGENTS", "cf83b9a4254a4140910e1bf50b3fd7d2")

    # Obtener agentes con URLs desde la DB 🤖 Agents
    services_with_url: dict[str, dict] = {}
    if NOTION_TOKEN:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{NOTION_BASE}/databases/{NOTION_DB_AGENTS}/query",
                    headers={"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"},
                    json={},
                    timeout=10,
                )
                if r.status_code == 200:
                    for page in r.json().get("results", []):
                        props = page.get("properties", {})
                        url = props.get("Service URL", {}).get("url")
                        if url:
                            title_parts = props.get("Name", {}).get("title", [])
                            name = "".join(t.get("plain_text", "") for t in title_parts).strip()
                            services_with_url[name] = {
                                "url": url,
                                "type": (props.get("Type", {}).get("select") or {}).get("name", "Custom"),
                            }
        except Exception:
            pass

    results_with_check: list[dict] = []
    results_registered: list[dict] = []
    loop = asyncio.get_event_loop()

    async with httpx.AsyncClient() as http:
        tasks = []
        agents_with_url = []

        for agent in ALL_AGENTS:
            svc = services_with_url.get(agent.name)
            if svc and svc.get("url"):
                tasks.append(
                    _check_and_report(
                        http, agent.name, svc["url"],
                        agent.category, agent.model, agent.priority, timeout,
                    )
                )
                agents_with_url.append(agent.name)

        if tasks:
            results_with_check = list(await asyncio.gather(*tasks))

    # Para agentes sin URL → marcar como Online (solo en catálogo)
    no_url_agents = [a for a in ALL_AGENTS if a.name not in agents_with_url]
    now_iso = datetime.now(timezone.utc).isoformat()

    def _bulk_register():
        for agent in no_url_agents:
            try:
                report_status(
                    name=agent.name,
                    category=agent.category,
                    model=agent.model,
                    priority=agent.priority,
                    estado="Online",
                    ultima_accion="Registered — no service URL configured",
                )
            except Exception:
                pass

    await loop.run_in_executor(None, _bulk_register)

    checked = len(results_with_check)
    errored = sum(1 for r in results_with_check if r["estado"] == "Error")

    return {
        "generated_at":    now_iso,
        "total_agents":    len(ALL_AGENTS),
        "health_checked":  checked,
        "registered_only": len(no_url_agents),
        "errors_detected": errored,
        "pct_ok":          round((checked - errored) / checked * 100) if checked else 100,
        "agents_checked":  results_with_check,
        "notion_url":      "https://www.notion.so/1ba923066cec454fbc9320995cfbaf7c",
    }
