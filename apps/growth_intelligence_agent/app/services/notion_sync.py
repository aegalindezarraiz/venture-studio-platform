"""
Sincronización del Growth Intelligence Agent con Notion.
Escribe Briefs y Tasks derivadas en las DBs correspondientes.
"""
import os
import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _post(path: str, payload: dict) -> dict:
    """Llama al backend que centraliza todas las escrituras en Notion."""
    try:
        r = httpx.post(f"{BACKEND_URL}/notion{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def push_brief(
    startup_id: str,
    startup_name: str,
    brief_content: str,
    agent_notion_id: str | None = None,
) -> dict:
    """Publica un Brief generado en la DB 📋 Briefs de Notion."""
    from datetime import datetime
    week = datetime.utcnow().strftime("%Y-W%W")
    result = _post("/briefs", {
        "name": f"Growth Brief — {startup_name} ({week})",
        "type": "Growth",
        "content": brief_content,
        "startup_id": startup_id,
        "agent_id": agent_notion_id,
    })
    return result


def push_tasks_from_brief(
    brief_content: str,
    startup_id: str,
    brief_notion_id: str | None = None,
    agent_notion_id: str | None = None,
) -> list[dict]:
    """
    Extrae tareas accionables del contenido del brief y las crea en ✅ Tasks.
    Busca líneas que empiecen con '- [ ]', '•', '1.', etc.
    """
    import re
    lines = brief_content.split("\n")
    task_pattern = re.compile(r"^[\-\*\•]?\s*\[?\s*\]?\s*(.+)$")

    tasks_created = []
    for line in lines:
        line = line.strip()
        # Solo líneas que parecen items accionables y no son encabezados
        if len(line) < 10 or line.startswith("#"):
            continue
        m = task_pattern.match(line)
        if m and any(kw in line.lower() for kw in ["implementa", "crea", "lanza", "define", "configura", "prueba", "analiza", "contacta", "publica"]):
            task_name = m.group(1)[:200]
            result = _post("/tasks", {
                "name": task_name,
                "startup_id": startup_id,
                "priority": "Alta",
                "created_by_agent": True,
                "agent_id": agent_notion_id,
            })
            tasks_created.append(result)
            if len(tasks_created) >= 5:  # Máx 5 tasks por brief
                break

    return tasks_created


def push_experiment(
    startup_id: str,
    name: str,
    hypothesis: str,
    channel: str,
    metric: str,
    brief_id: str | None = None,
) -> dict:
    """Crea un experimento en 🧪 Experiments derivado del brief."""
    return _post("/experiments", {
        "name": name,
        "hypothesis": hypothesis,
        "channel": channel,
        "metric": metric,
        "startup_id": startup_id,
        "brief_id": brief_id,
    })
