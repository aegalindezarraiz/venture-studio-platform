"""
monitor_service.py — Sincronización del estado de los 500 agentes
con la DB '🤖 Monitor de Agentes' de Notion.

Funciones principales:
  • seed_monitor()          — Crea/actualiza las 500 entradas en Notion
  • report_status()         — Actualiza estado de un agente individual
  • get_monitor_overview()  — Resumen de estados desde Notion
  • _load_page_map()        — Cache name → page_id para evitar N+1 queries
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("monitor-service")

MONITOR_DB_ID = os.environ.get("NOTION_DB_MONITOR", "1ba923066cec454fbc9320995cfbaf7c")

# ── Cache en memoria: agent_name → notion_page_id ─────────────────────────────
# Se construye la primera vez que se usa seed o report.
_page_map: dict[str, str] = {}
_page_map_loaded = False


def _client():
    from notion_client import Client
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN no configurado")
    return Client(auth=token)


def _priority_label(priority: int) -> str:
    return {1: "1 - Crítico", 2: "2 - Normal", 3: "3 - Soporte"}.get(priority, "2 - Normal")


def _load_page_map(client) -> dict[str, str]:
    """Consulta todas las páginas del Monitor DB y devuelve {nombre: page_id}."""
    global _page_map, _page_map_loaded
    mapping: dict[str, str] = {}
    has_more = True
    cursor = None

    while has_more:
        kwargs: dict = {"database_id": MONITOR_DB_ID, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        r = client.databases.query(**kwargs)
        for page in r.get("results", []):
            props = page.get("properties", {})
            title_parts = props.get("Nombre del Agente", {}).get("title", [])
            name = "".join(t.get("plain_text", "") for t in title_parts).strip()
            if name:
                mapping[name] = page["id"]
        has_more = r.get("has_more", False)
        cursor = r.get("next_cursor")

    _page_map = mapping
    _page_map_loaded = True
    return mapping


def _build_properties(
    name: str,
    category: str,
    model: str,
    priority: int,
    estado: str,
    ultima_accion: str,
    latencia_ms: Optional[int],
    runs_total: Optional[int],
) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    props: dict = {
        "Nombre del Agente": {"title": [{"text": {"content": name}}]},
        "Estado":            {"select": {"name": estado}},
        "Categoría":         {"select": {"name": category}},
        "Modelo":            {"select": {"name": model}},
        "Prioridad":         {"select": {"name": _priority_label(priority)}},
        "Última Acción":     {"rich_text": [{"text": {"content": ultima_accion[:2000]}}]},
        "Última Actualización": {"date": {"start": now_iso}},
    }
    if latencia_ms is not None:
        props["Latencia (ms)"] = {"number": latencia_ms}
    if runs_total is not None:
        props["Runs Total"] = {"number": runs_total}
    return props


# ── API pública ───────────────────────────────────────────────────────────────

def report_status(
    name: str,
    category: str,
    model: str,
    priority: int,
    estado: str = "Online",
    ultima_accion: str = "",
    latencia_ms: Optional[int] = None,
    runs_total: Optional[int] = None,
) -> dict:
    """
    Actualiza en tiempo real el estado de un agente en el Monitor de Agentes.
    Usa el cache _page_map para no hacer un query por cada llamada.
    """
    global _page_map
    client = _client()

    if not _page_map_loaded:
        _load_page_map(client)

    props = _build_properties(name, category, model, priority, estado, ultima_accion, latencia_ms, runs_total)

    page_id = _page_map.get(name)
    if page_id:
        client.pages.update(page_id=page_id, properties=props)
        return {"action": "updated", "page_id": page_id, "agent": name}
    else:
        page = client.pages.create(parent={"database_id": MONITOR_DB_ID}, properties=props)
        _page_map[name] = page["id"]
        return {"action": "created", "page_id": page["id"], "agent": name}


def seed_monitor(batch_size: int = 10) -> dict:
    """
    Registra/actualiza los 500 agentes en el Monitor de Agentes.
    Estrategia eficiente:
      1. Carga todas las páginas existentes (5-6 queries a Notion)
      2. Recorre los 500 agentes haciendo create o update según corresponda
      3. Pausa cada `batch_size` agentes para respetar el rate limit de Notion
    """
    import time
    from packages.agents.definitions import ALL_AGENTS

    client = _client()
    log.info("Cargando mapa de páginas existentes en Monitor DB...")
    existing = _load_page_map(client)
    log.info(f"Encontradas {len(existing)} entradas previas en el Monitor.")

    created = updated = errors = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for i, agent in enumerate(ALL_AGENTS):
        try:
            props = _build_properties(
                name=agent.name,
                category=agent.category,
                model=agent.model,
                priority=agent.priority,
                estado="Online",
                ultima_accion=agent.role,
                latencia_ms=None,
                runs_total=0,
            )
            # Forzar timestamp de seed
            props["Última Actualización"] = {"date": {"start": now_iso}}

            if agent.name in existing:
                client.pages.update(page_id=existing[agent.name], properties=props)
                updated += 1
            else:
                page = client.pages.create(parent={"database_id": MONITOR_DB_ID}, properties=props)
                _page_map[agent.name] = page["id"]
                created += 1

        except Exception as e:
            log.warning(f"Error seed monitor [{agent.id}]: {e}")
            errors += 1

        if (i + 1) % batch_size == 0:
            time.sleep(0.35)   # ~2.8 req/s — bien bajo el límite de 3 req/s de Notion

    log.info(f"Seed completado: created={created} updated={updated} errors={errors}")
    return {
        "created": created,
        "updated": updated,
        "errors":  errors,
        "total":   len(ALL_AGENTS),
        "db_id":   MONITOR_DB_ID,
    }


def get_monitor_overview() -> dict:
    """Consulta el Monitor DB y retorna un resumen de estados y categorías."""
    client = _client()
    all_pages: list = []
    has_more = True
    cursor = None

    while has_more:
        kwargs: dict = {"database_id": MONITOR_DB_ID, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        r = client.databases.query(**kwargs)
        all_pages.extend(r.get("results", []))
        has_more = r.get("has_more", False)
        cursor = r.get("next_cursor")

    estados: dict[str, int] = {"Online": 0, "Trabajando": 0, "Error": 0}
    categorias: dict[str, int] = {}
    errores: list[dict] = []

    for page in all_pages:
        props = page.get("properties", {})

        estado_sel = props.get("Estado", {}).get("select")
        estado = estado_sel.get("name") if estado_sel else "Sin estado"
        estados[estado] = estados.get(estado, 0) + 1

        cat_sel = props.get("Categoría", {}).get("select")
        cat = cat_sel.get("name") if cat_sel else "sin_categoría"
        categorias[cat] = categorias.get(cat, 0) + 1

        if estado == "Error":
            title_parts = props.get("Nombre del Agente", {}).get("title", [])
            name = "".join(t.get("plain_text", "") for t in title_parts).strip()
            accion_parts = props.get("Última Acción", {}).get("rich_text", [])
            accion = "".join(t.get("plain_text", "") for t in accion_parts).strip()
            errores.append({"name": name, "ultima_accion": accion})

    total = len(all_pages)
    return {
        "total":        total,
        "estados":      estados,
        "categorias":   categorias,
        "agentes_error": errores,
        "pct_online":   round(estados.get("Online", 0) / total * 100) if total else 0,
        "pct_error":    round(estados.get("Error", 0) / total * 100) if total else 0,
        "notion_url":   f"https://www.notion.so/{MONITOR_DB_ID.replace('-', '')}",
    }
