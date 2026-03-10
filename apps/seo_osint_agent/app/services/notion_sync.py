"""
Sincronización del SEO/OSINT Agent con Notion.
Convierte oportunidades detectadas en Experiments y Tasks.
"""
import os
import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _post(path: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{BACKEND_URL}/notion{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def push_seo_opportunity(
    startup_id: str,
    keyword: str,
    search_volume: int,
    difficulty: int,
    competitor: str | None = None,
) -> dict:
    """
    Crea un experimento SEO en Notion cuando se detecta una oportunidad de keyword.
    """
    difficulty_label = "baja" if difficulty < 30 else "media" if difficulty < 60 else "alta"
    hypothesis = (
        f"Si creamos contenido optimizado para '{keyword}' "
        f"(vol: {search_volume:,}/mes, dificultad {difficulty_label})"
        + (f", compitiendo con {competitor}" if competitor else "")
        + ", entonces aumentamos el tráfico orgánico y mejoramos la conversión."
    )

    experiment = _post("/experiments", {
        "name": f"SEO — {keyword}",
        "hypothesis": hypothesis,
        "channel": "SEO",
        "metric": "Conversión",
        "startup_id": startup_id,
    })

    # Crear task accionable asociada
    if "id" in experiment:
        _post("/tasks", {
            "name": f"Crear artículo para keyword: {keyword}",
            "startup_id": startup_id,
            "priority": "Alta" if difficulty < 40 else "Media",
            "created_by_agent": True,
        })

    return experiment


def push_competitor_signal(
    startup_id: str,
    competitor_name: str,
    signal_type: str,
    description: str,
) -> dict:
    """
    Registra una señal de inteligencia competitiva como experimento OSINT.
    signal_type: 'pricing_change' | 'new_feature' | 'funding' | 'content'
    """
    channel_map = {
        "pricing_change": "Product",
        "new_feature": "Product",
        "funding": "Community",
        "content": "SEO",
    }
    channel = channel_map.get(signal_type, "SEO")

    hypothesis = (
        f"Señal detectada en {competitor_name}: {signal_type}. "
        f"Detalles: {description}. "
        "Si reaccionamos tácticamente a este movimiento, podemos capturar usuarios descontentos o ganar ventaja de posicionamiento."
    )

    return _post("/experiments", {
        "name": f"OSINT — {competitor_name}: {signal_type}",
        "hypothesis": hypothesis,
        "channel": channel,
        "metric": "Conversión",
        "startup_id": startup_id,
    })
