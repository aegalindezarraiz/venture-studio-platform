"""
Servicio central de Notion — AI Venture Studio OS.
Todas las operaciones de lectura/escritura sobre las 7 DBs pasan por aquí.
"""
import os
from datetime import datetime
from typing import Any

from notion_client import Client

# ── IDs de las 7 bases de datos ───────────────────────────────────────────────
DB = {
    "startups":       os.environ.get("NOTION_DB_STARTUPS",       "460c359a4f8849bd9c9a003e7520e7c0"),
    "okrs":           os.environ.get("NOTION_DB_OKRS",           "6575a70444b7404f87f1b1161b21748a"),
    "tasks":          os.environ.get("NOTION_DB_TASKS",          "1a166396f42a806ea9e1c2512f451f28"),
    "experiments":    os.environ.get("NOTION_DB_EXPERIMENTS",    "c00a6a2cde6243e9af6c4c636b5a7d14"),
    "briefs":         os.environ.get("NOTION_DB_BRIEFS",         "7956591d7f774ad69ac0bf8faeec02ac"),
    "agents":         os.environ.get("NOTION_DB_AGENTS",         "cf83b9a4254a4140910e1bf50b3fd7d2"),
    "weekly_reviews": os.environ.get("NOTION_DB_WEEKLY_REVIEWS", "465c28a2359f449ba3865dd15df0a683"),
}


def _client() -> Client:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN no configurado")
    return Client(auth=token)


def _title(text: str) -> list:
    return [{"text": {"content": text}}]


def _rich_text(text: str) -> list:
    return [{"text": {"content": text[:2000]}}]  # Notion max 2000 chars por bloque


def _relation(page_id: str) -> list:
    return [{"id": page_id}]


def _extract_title(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            parts = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in parts).strip()
    return ""


def _extract_select(page: dict, key: str) -> str | None:
    prop = page.get("properties", {}).get(key, {})
    sel = prop.get("select")
    return sel.get("name") if sel else None


def _extract_number(page: dict, key: str) -> float | None:
    prop = page.get("properties", {}).get(key, {})
    return prop.get("number")


# ── STARTUPS ──────────────────────────────────────────────────────────────────

def get_startups(status: str | None = None) -> list[dict]:
    notion = _client()
    filters = []
    if status:
        filters.append({"property": "Status", "select": {"equals": status}})

    params: dict[str, Any] = {"database_id": DB["startups"]}
    if filters:
        params["filter"] = {"and": filters}

    response = notion.databases.query(**params)
    return [
        {
            "id": p["id"],
            "name": _extract_title(p),
            "stage": _extract_select(p, "Stage"),
            "status": _extract_select(p, "Status"),
            "mrr": _extract_number(p, "MRR"),
            "score": _extract_number(p, "Score"),
            "url": p.get("url"),
        }
        for p in response.get("results", [])
    ]


def get_startup(startup_id: str) -> dict:
    notion = _client()
    page = notion.pages.retrieve(startup_id)
    return {
        "id": page["id"],
        "name": _extract_title(page),
        "stage": _extract_select(page, "Stage"),
        "status": _extract_select(page, "Status"),
        "mrr": _extract_number(page, "MRR"),
        "score": _extract_number(page, "Score"),
    }


def update_startup_score(startup_id: str, score: float) -> dict:
    notion = _client()
    return notion.pages.update(
        startup_id,
        properties={"Score": {"number": score}},
    )


# ── OKRs ──────────────────────────────────────────────────────────────────────

def get_okrs(startup_id: str | None = None, status: str | None = None) -> list[dict]:
    notion = _client()
    filters = []
    if startup_id:
        filters.append({"property": "Startup", "relation": {"contains": startup_id}})
    if status:
        filters.append({"property": "Status", "select": {"equals": status}})

    params: dict[str, Any] = {"database_id": DB["okrs"]}
    if filters:
        params["filter"] = {"and": filters} if len(filters) > 1 else filters[0]

    response = notion.databases.query(**params)
    return [
        {
            "id": p["id"],
            "name": _extract_title(p),
            "status": _extract_select(p, "Status"),
            "type": _extract_select(p, "Type"),
            "quarter": _extract_select(p, "Quarter"),
            "progress": _extract_number(p, "Progress"),
        }
        for p in response.get("results", [])
    ]


def create_okr(name: str, startup_id: str, quarter: str, okr_type: str = "Objetivo") -> dict:
    notion = _client()
    props: dict[str, Any] = {
        "Name": {"title": _title(name)},
        "Quarter": {"select": {"name": quarter}},
        "Type": {"select": {"name": okr_type}},
        "Status": {"select": {"name": "On track"}},
        "Progress": {"number": 0},
    }
    if startup_id:
        props["Startup"] = {"relation": _relation(startup_id)}

    page = notion.pages.create(parent={"database_id": DB["okrs"]}, properties=props)
    return {"id": page["id"], "name": name}


def update_okr(okr_id: str, status: str | None = None, progress: float | None = None) -> dict:
    notion = _client()
    props: dict[str, Any] = {}
    if status:
        props["Status"] = {"select": {"name": status}}
    if progress is not None:
        props["Progress"] = {"number": progress}
    return notion.pages.update(okr_id, properties=props)


# ── TASKS ─────────────────────────────────────────────────────────────────────

def get_tasks(startup_id: str | None = None, status: str | None = None) -> list[dict]:
    notion = _client()
    filters = []
    if startup_id:
        filters.append({"property": "Startup", "relation": {"contains": startup_id}})
    if status:
        filters.append({"property": "Status", "select": {"equals": status}})

    params: dict[str, Any] = {"database_id": DB["tasks"]}
    if filters:
        params["filter"] = {"and": filters} if len(filters) > 1 else filters[0]

    response = notion.databases.query(**params)
    return [
        {
            "id": p["id"],
            "name": _extract_title(p),
            "status": _extract_select(p, "Status"),
            "priority": _extract_select(p, "Priority"),
        }
        for p in response.get("results", [])
    ]


def create_task(
    name: str,
    startup_id: str | None = None,
    okr_id: str | None = None,
    priority: str = "Media",
    created_by_agent: bool = False,
    agent_id: str | None = None,
) -> dict:
    notion = _client()
    props: dict[str, Any] = {
        "Name": {"title": _title(name)},
        "Priority": {"select": {"name": f"🟡 {priority}" if priority == "Media" else f"🔴 {priority}" if priority == "Alta" else f"🟢 {priority}"}},
        "Status": {"select": {"name": "Backlog"}},
        "Created by Agent": {"checkbox": created_by_agent},
    }
    if startup_id:
        props["Startup"] = {"relation": _relation(startup_id)}
    if okr_id:
        props["OKR"] = {"relation": _relation(okr_id)}
    if agent_id:
        props["Agent"] = {"relation": _relation(agent_id)}

    page = notion.pages.create(parent={"database_id": DB["tasks"]}, properties=props)
    return {"id": page["id"], "name": name}


# ── BRIEFS ────────────────────────────────────────────────────────────────────

def create_brief(
    name: str,
    brief_type: str,
    content: str,
    startup_id: str | None = None,
    agent_id: str | None = None,
) -> dict:
    notion = _client()
    props: dict[str, Any] = {
        "Name": {"title": _title(name)},
        "Type": {"select": {"name": brief_type}},
        "Status": {"select": {"name": "Listo"}},
        "Generated At": {"date": {"start": datetime.utcnow().date().isoformat()}},
    }
    if startup_id:
        props["Startup"] = {"relation": _relation(startup_id)}
    if agent_id:
        props["Agent"] = {"relation": _relation(agent_id)}

    # Contenido como bloque de párrafo (puede exceder 2000 chars → dividir)
    children = []
    for i in range(0, len(content), 1900):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(content[i:i + 1900])},
        })

    page = notion.pages.create(
        parent={"database_id": DB["briefs"]},
        properties=props,
        children=children or [{"object": "block", "type": "paragraph",
                                "paragraph": {"rich_text": _rich_text("(sin contenido)")}}],
    )
    return {"id": page["id"], "name": name, "url": page.get("url")}


def update_brief_status(brief_id: str, status: str) -> dict:
    notion = _client()
    return notion.pages.update(brief_id, properties={"Status": {"select": {"name": status}}})


# ── EXPERIMENTS ───────────────────────────────────────────────────────────────

def create_experiment(
    name: str,
    hypothesis: str,
    channel: str,
    metric: str,
    startup_id: str | None = None,
    brief_id: str | None = None,
) -> dict:
    notion = _client()
    props: dict[str, Any] = {
        "Name": {"title": _title(name)},
        "Hypothesis": {"rich_text": _rich_text(hypothesis)},
        "Channel": {"select": {"name": channel}},
        "Metric": {"select": {"name": metric}},
        "Status": {"select": {"name": "Idea"}},
        "Start Date": {"date": {"start": datetime.utcnow().date().isoformat()}},
    }
    if startup_id:
        props["Startup"] = {"relation": _relation(startup_id)}
    if brief_id:
        props["Brief"] = {"relation": _relation(brief_id)}

    page = notion.pages.create(parent={"database_id": DB["experiments"]}, properties=props)
    return {"id": page["id"], "name": name}


def update_experiment_result(experiment_id: str, result: float, winner: bool = False) -> dict:
    notion = _client()
    return notion.pages.update(
        experiment_id,
        properties={
            "Result": {"number": result},
            "Winner": {"checkbox": winner},
            "Status": {"select": {"name": "Completado"}},
        },
    )


# ── AGENTS ────────────────────────────────────────────────────────────────────

def get_agents(status: str | None = "Activo") -> list[dict]:
    notion = _client()
    params: dict[str, Any] = {"database_id": DB["agents"]}
    if status:
        params["filter"] = {"property": "Status", "select": {"equals": status}}
    response = notion.databases.query(**params)
    return [
        {
            "id": p["id"],
            "name": _extract_title(p),
            "type": _extract_select(p, "Type"),
            "status": _extract_select(p, "Status"),
            "model": _extract_select(p, "Model"),
            "runs_total": _extract_number(p, "Runs Total"),
        }
        for p in response.get("results", [])
    ]


def upsert_agent(name: str, agent_type: str, service_url: str, model: str = "claude-sonnet-4-6") -> dict:
    """Crea el agente en Notion si no existe; si existe, lo actualiza."""
    notion = _client()
    response = notion.databases.query(
        database_id=DB["agents"],
        filter={"property": "Name", "title": {"equals": name}},
    )
    props: dict[str, Any] = {
        "Name": {"title": _title(name)},
        "Type": {"select": {"name": agent_type}},
        "Service URL": {"url": service_url},
        "Model": {"select": {"name": model}},
        "Status": {"select": {"name": "Activo"}},
    }
    if response.get("results"):
        page_id = response["results"][0]["id"]
        notion.pages.update(page_id, properties=props)
        return {"id": page_id, "name": name, "action": "updated"}
    else:
        props["Runs Total"] = {"number": 0}
        page = notion.pages.create(parent={"database_id": DB["agents"]}, properties=props)
        return {"id": page["id"], "name": name, "action": "created"}


def record_agent_run(agent_id: str) -> dict:
    """Incrementa Runs Total y actualiza Last Run."""
    notion = _client()
    page = notion.pages.retrieve(agent_id)
    current_runs = _extract_number(page, "Runs Total") or 0
    return notion.pages.update(
        agent_id,
        properties={
            "Last Run": {"date": {"start": datetime.utcnow().isoformat()}},
            "Runs Total": {"number": current_runs + 1},
        },
    )


# ── WEEKLY REVIEWS ────────────────────────────────────────────────────────────

def create_weekly_review(
    week_name: str,
    highlights: str,
    blockers: str,
    health_score: float,
    startup_ids: list[str] | None = None,
) -> dict:
    notion = _client()
    props: dict[str, Any] = {
        "Name": {"title": _title(week_name)},
        "Date": {"date": {"start": datetime.utcnow().date().isoformat()}},
        "Highlights": {"rich_text": _rich_text(highlights)},
        "Blockers": {"rich_text": _rich_text(blockers)},
        "Health Score Studio": {"number": health_score},
    }
    if startup_ids:
        props["Startups Reviewed"] = {"relation": [{"id": sid} for sid in startup_ids]}

    page = notion.pages.create(parent={"database_id": DB["weekly_reviews"]}, properties=props)
    return {"id": page["id"], "name": week_name, "url": page.get("url")}
