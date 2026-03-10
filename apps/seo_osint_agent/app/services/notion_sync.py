"""Sincronización del SEO/OSINT Agent con Notion."""
import os
import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
_agent_notion_id: str | None = None


def _post(path: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{BACKEND_URL}/notion{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def register_self() -> str | None:
    global _agent_notion_id
    result = _post("/agents", {
        "name": "SEO & OSINT Agent",
        "type": "SEO/OSINT",
        "service_url": os.environ.get("SEO_OSINT_AGENT_URL", "http://seo_osint_agent:8003"),
        "model": os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6"),
    })
    _agent_notion_id = result.get("id")
    return _agent_notion_id


def push_seo_opportunity(
    startup_id: str,
    keyword: str,
    search_volume: int,
    difficulty: int,
    competitor: str | None = None,
) -> dict:
    difficulty_label = "baja" if difficulty < 30 else "media" if difficulty < 60 else "alta"
    hypothesis = (
        f"Si creamos contenido optimizado para '{keyword}' "
        f"(vol: {search_volume:,}/mes, dificultad {difficulty_label})"
        + (f", compitiendo directamente con {competitor}" if competitor else "")
        + ", entonces aumentamos el tráfico orgánico y mejoramos la tasa de conversión."
    )
    experiment = _post("/experiments", {
        "name": f"SEO — {keyword}",
        "hypothesis": hypothesis,
        "channel": "SEO",
        "metric": "Conversión",
        "startup_id": startup_id,
    })
    if "id" in experiment:
        _post("/tasks", {
            "name": f"Crear artículo optimizado: {keyword}",
            "startup_id": startup_id,
            "priority": "Alta" if difficulty < 40 else "Media",
            "created_by_agent": True,
            "agent_id": _agent_notion_id,
        })
    return experiment


def push_competitor_signal(
    startup_id: str,
    competitor_name: str,
    signal_type: str,
    description: str,
) -> dict:
    channel_map = {
        "pricing_change": "Product",
        "new_feature": "Product",
        "funding": "Community",
        "content": "SEO",
    }
    return _post("/experiments", {
        "name": f"OSINT — {competitor_name}: {signal_type}",
        "hypothesis": (
            f"Señal detectada en {competitor_name} ({signal_type}): {description}. "
            "Reaccionar tácticamente puede capturar usuarios descontentos o ganar ventaja."
        ),
        "channel": channel_map.get(signal_type, "SEO"),
        "metric": "Conversión",
        "startup_id": startup_id,
    })
