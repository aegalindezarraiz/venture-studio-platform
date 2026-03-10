"""
registry.py — AgentRegistry: gestión en memoria + sincronización con Notion.

Responsabilidades:
  • Fuente de verdad de los 500 agentes (definitions.py)
  • Filtrado, búsqueda y paginación
  • Sincronización con la DB 🤖 Agents de Notion
  • Estado en tiempo real (ready / degraded / inactive)
"""
import logging
import os
from typing import Optional

import httpx

from packages.agents.definitions import (
    ALL_AGENTS, AGENTS_BY_CATEGORY, AGENTS_BY_ID, AgentDef
)

log = logging.getLogger("agent-registry")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────────────
# Estado en tiempo real (en memoria, actualizado por health checks)
# ─────────────────────────────────────────────────────────────────────────────

_runtime_status: dict[str, dict] = {}   # agent_id → {ready, latency_ms, error}


def set_agent_status(agent_id: str, ready: bool, latency_ms: int | None = None, error: str | None = None):
    _runtime_status[agent_id] = {"ready": ready, "latency_ms": latency_ms, "error": error}


def get_agent_status(agent_id: str) -> dict:
    return _runtime_status.get(agent_id, {"ready": None, "latency_ms": None, "error": "not_checked"})


# ─────────────────────────────────────────────────────────────────────────────
# Consultas
# ─────────────────────────────────────────────────────────────────────────────

def get_all(
    category: Optional[str] = None,
    priority: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Retorna agentes filtrados y paginados.
    Args:
        category:  filtrar por categoría
        priority:  filtrar por prioridad (1=crítico, 2=normal, 3=soporte)
        search:    búsqueda en name, role y description
        page:      número de página (1-indexed)
        page_size: tamaño de página (max 100)
    """
    agents = ALL_AGENTS

    if category:
        agents = AGENTS_BY_CATEGORY.get(category.lower(), [])

    if priority:
        agents = [a for a in agents if a.priority == priority]

    if search:
        q = search.lower()
        agents = [
            a for a in agents
            if q in a.name.lower() or q in a.role.lower() or q in a.description.lower()
               or any(q in cap for cap in a.capabilities)
        ]

    total = len(agents)
    page_size = min(page_size, 100)
    start = (page - 1) * page_size
    end = start + page_size
    page_agents = agents[start:end]

    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "pages":     (total + page_size - 1) // page_size,
        "agents":    [_serialize(a) for a in page_agents],
    }


def get_by_id(agent_id: str) -> Optional[dict]:
    agent = AGENTS_BY_ID.get(agent_id)
    return _serialize(agent) if agent else None


def get_summary() -> dict:
    """Resumen por categoría con conteos y estado."""
    categories = {}
    for cat, agents in AGENTS_BY_CATEGORY.items():
        statuses = [_runtime_status.get(a.id, {}) for a in agents]
        ready    = sum(1 for s in statuses if s.get("ready") is True)
        checked  = sum(1 for s in statuses if s.get("ready") is not None)
        categories[cat] = {
            "total":     len(agents),
            "ready":     ready,
            "checked":   checked,
            "unchecked": len(agents) - checked,
            "pct_ready": round(ready / checked * 100) if checked else None,
            "priority_1": sum(1 for a in agents if a.priority == 1),
        }

    total_ready   = sum(v["ready"]   for v in categories.values())
    total_checked = sum(v["checked"] for v in categories.values())

    return {
        "total_agents":   len(ALL_AGENTS),
        "total_ready":    total_ready,
        "total_checked":  total_checked,
        "pct_ready":      round(total_ready / total_checked * 100) if total_checked else None,
        "categories":     categories,
    }


def _serialize(agent: AgentDef) -> dict:
    status = _runtime_status.get(agent.id, {})
    return {
        "id":           agent.id,
        "name":         agent.name,
        "category":     agent.category,
        "role":         agent.role,
        "description":  agent.description,
        "capabilities": agent.capabilities,
        "model":        agent.model,
        "tools":        agent.tools,
        "priority":     agent.priority,
        "system_prompt": agent.system_prompt,
        "runtime": {
            "ready":      status.get("ready"),
            "latency_ms": status.get("latency_ms"),
            "error":      status.get("error"),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Seed a Notion
# ─────────────────────────────────────────────────────────────────────────────

def seed_to_notion(batch_size: int = 10) -> dict:
    """
    Registra / actualiza todos los 500 agentes en la DB 🤖 Agents de Notion.
    Envía en batches para respetar el rate limit de Notion.
    """
    import time
    created = 0
    updated = 0
    errors  = 0

    for i, agent in enumerate(ALL_AGENTS):
        try:
            r = httpx.post(
                f"{BACKEND_URL}/notion/agents",
                json={
                    "name":        f"[{agent.category.upper()}] {agent.role}",
                    "type":        _notion_type(agent.category),
                    "service_url": f"{BACKEND_URL}/agents/{agent.id}",
                    "model":       agent.model,
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            if data.get("action") == "created":
                created += 1
            else:
                updated += 1
        except Exception as e:
            log.warning(f"Error seed agente {agent.id}: {e}")
            errors += 1

        # Rate limit: pausa cada batch_size requests
        if (i + 1) % batch_size == 0:
            time.sleep(0.4)

    return {"created": created, "updated": updated, "errors": errors, "total": len(ALL_AGENTS)}


def _notion_type(category: str) -> str:
    mapping = {
        "executive":   "Supervisor",
        "product":     "Custom",
        "engineering": "Runtime",
        "growth":      "Growth",
        "data":        "Custom",
        "security":    "Custom",
        "osint":       "SEO/OSINT",
    }
    return mapping.get(category, "Custom")
