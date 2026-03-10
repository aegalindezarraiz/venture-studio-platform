"""
test_agents.py — Verificación masiva de agentes del AI Venture Studio OS.

Lee todos los agentes registrados en la DB 🤖 Agents de Notion,
verifica en paralelo:
  • Conectividad con la API de Notion (lectura de cada DB)
  • Health endpoint de cada servicio (Service URL/health)
  • Frescura de ejecución (Last Run < umbral configurable)

Uso:
  python scripts/test_agents.py
  python scripts/test_agents.py --timeout 5 --max-age-hours 24 --report report.json
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Logging estructurado ──────────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("agent-tester")

# Colores ANSI para terminal
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _green(t):  return f"{GREEN}{t}{RESET}"
def _red(t):    return f"{RED}{t}{RESET}"
def _yellow(t): return f"{YELLOW}{t}{RESET}"
def _cyan(t):   return f"{CYAN}{t}{RESET}"
def _bold(t):   return f"{BOLD}{t}{RESET}"


# ── Notion helpers ────────────────────────────────────────────────────────────

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_AGENTS = os.environ.get("NOTION_DB_AGENTS", "cf83b9a4254a4140910e1bf50b3fd7d2")
NOTION_VERSION = "2022-06-28"
NOTION_BASE = "https://api.notion.com/v1"

NOTION_DBS = {
    "startups":       os.environ.get("NOTION_DB_STARTUPS",       "460c359a4f8849bd9c9a003e7520e7c0"),
    "okrs":           os.environ.get("NOTION_DB_OKRS",           "6575a70444b7404f87f1b1161b21748a"),
    "tasks":          os.environ.get("NOTION_DB_TASKS",          "1a166396f42a806ea9e1c2512f451f28"),
    "experiments":    os.environ.get("NOTION_DB_EXPERIMENTS",    "c00a6a2cde6243e9af6c4c636b5a7d14"),
    "briefs":         os.environ.get("NOTION_DB_BRIEFS",         "7956591d7f774ad69ac0bf8faeec02ac"),
    "agents":         NOTION_DB_AGENTS,
    "weekly_reviews": os.environ.get("NOTION_DB_WEEKLY_REVIEWS", "465c28a2359f449ba3865dd15df0a683"),
}


def _notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _extract_title(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", [])).strip()
    return "(sin nombre)"


def _extract_select(page: dict, key: str) -> str | None:
    prop = page.get("properties", {}).get(key, {})
    sel = prop.get("select")
    return sel.get("name") if sel else None


def _extract_url(page: dict, key: str) -> str | None:
    prop = page.get("properties", {}).get(key, {})
    return prop.get("url")


def _extract_date(page: dict, key: str) -> str | None:
    prop = page.get("properties", {}).get(key, {})
    d = prop.get("date")
    return d.get("start") if d else None


def _extract_number(page: dict, key: str) -> float | None:
    prop = page.get("properties", {}).get(key, {})
    return prop.get("number")


# ── Lectura de agentes desde Notion ──────────────────────────────────────────

async def fetch_agents_from_notion(client: httpx.AsyncClient) -> list[dict]:
    """Lee todos los agentes registrados en la DB 🤖 Agents."""
    if not NOTION_TOKEN:
        log.error("NOTION_TOKEN no configurado — no se puede leer la DB de agentes")
        return []
    try:
        r = await client.post(
            f"{NOTION_BASE}/databases/{NOTION_DB_AGENTS}/query",
            headers=_notion_headers(),
            json={},
            timeout=15,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        agents = []
        for page in results:
            agents.append({
                "id":          page["id"],
                "name":        _extract_title(page),
                "type":        _extract_select(page, "Type"),
                "status":      _extract_select(page, "Status"),
                "model":       _extract_select(page, "Model"),
                "service_url": _extract_url(page, "Service URL"),
                "last_run":    _extract_date(page, "Last Run"),
                "runs_total":  _extract_number(page, "Runs Total"),
            })
        return agents
    except Exception as e:
        log.error(f"Error leyendo agentes de Notion: {e}")
        return []


# ── Checks individuales ───────────────────────────────────────────────────────

async def check_notion_db(client: httpx.AsyncClient, db_name: str, db_id: str) -> dict:
    """Verifica que una DB de Notion es accesible."""
    start = time.perf_counter()
    try:
        r = await client.get(
            f"{NOTION_BASE}/databases/{db_id}",
            headers=_notion_headers(),
            timeout=10,
        )
        latency_ms = round((time.perf_counter() - start) * 1000)
        if r.status_code == 200:
            return {"db": db_name, "status": "ok", "latency_ms": latency_ms}
        else:
            return {"db": db_name, "status": "error", "http": r.status_code, "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000)
        return {"db": db_name, "status": "error", "error": str(e), "latency_ms": latency_ms}


async def check_agent_health(
    client: httpx.AsyncClient,
    agent: dict,
    timeout: float,
    max_age_hours: int,
) -> dict:
    """
    Verifica el health endpoint del agente.
    Retorna un resultado estructurado con estado y diagnóstico.
    """
    name = agent["name"]
    service_url = agent.get("service_url", "").rstrip("/")
    result = {
        "id":          agent["id"],
        "name":        name,
        "type":        agent.get("type"),
        "model":       agent.get("model"),
        "service_url": service_url,
        "status":      agent.get("status"),
        "runs_total":  agent.get("runs_total", 0),
        "last_run":    agent.get("last_run"),
        "checks":      {},
        "ready":       False,
        "issues":      [],
    }

    # Check 1: Service URL definida
    if not service_url:
        result["issues"].append("Service URL no configurada en Notion")
        result["checks"]["url_configured"] = False
        return result
    result["checks"]["url_configured"] = True

    # Check 2: Health endpoint responde
    start = time.perf_counter()
    try:
        r = await client.get(f"{service_url}/health", timeout=timeout)
        latency_ms = round((time.perf_counter() - start) * 1000)
        if r.status_code == 200:
            result["checks"]["health_endpoint"] = {"ok": True, "latency_ms": latency_ms}
            body = r.json()
            result["health_response"] = body
        else:
            result["checks"]["health_endpoint"] = {"ok": False, "http": r.status_code}
            result["issues"].append(f"Health devolvió HTTP {r.status_code}")
    except httpx.ConnectError:
        result["checks"]["health_endpoint"] = {"ok": False, "error": "connection_refused"}
        result["issues"].append(f"No se puede conectar a {service_url}")
    except httpx.TimeoutException:
        result["checks"]["health_endpoint"] = {"ok": False, "error": "timeout"}
        result["issues"].append(f"Timeout ({timeout}s) en {service_url}/health")
    except Exception as e:
        result["checks"]["health_endpoint"] = {"ok": False, "error": str(e)}
        result["issues"].append(str(e))

    # Check 3: Frescura de Last Run
    if agent.get("last_run"):
        try:
            last = datetime.fromisoformat(agent["last_run"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours_ago = (now - last).total_seconds() / 3600
            fresh = hours_ago <= max_age_hours
            result["checks"]["last_run_fresh"] = {
                "ok": fresh,
                "hours_ago": round(hours_ago, 1),
                "threshold_hours": max_age_hours,
            }
            if not fresh:
                result["issues"].append(f"Sin ejecución en {hours_ago:.1f}h (umbral: {max_age_hours}h)")
        except Exception:
            result["checks"]["last_run_fresh"] = {"ok": None, "error": "parse_error"}
    else:
        result["checks"]["last_run_fresh"] = {"ok": None, "note": "nunca ejecutado"}

    # Check 4: Status en Notion
    notion_status = agent.get("status", "")
    result["checks"]["notion_status"] = {
        "ok": notion_status == "Activo",
        "value": notion_status,
    }
    if notion_status != "Activo":
        result["issues"].append(f"Status en Notion: '{notion_status}' (esperado: Activo)")

    # ¿Listo? Solo si health OK y sin errores críticos de conexión
    health_ok = result["checks"].get("health_endpoint", {}).get("ok", False)
    result["ready"] = health_ok
    return result


# ── Runner principal ──────────────────────────────────────────────────────────

async def run_tests(timeout: float, max_age_hours: int) -> dict:
    log.info(_bold("=" * 60))
    log.info(_bold("  AI Venture Studio OS — Test de Agentes"))
    log.info(_bold("=" * 60))
    started_at = datetime.utcnow().isoformat()

    async with httpx.AsyncClient() as client:

        # ── 1. Verificar conectividad con las 7 DBs de Notion ────────────────
        log.info(_cyan("\n[1/3] Verificando conectividad con las 7 DBs de Notion..."))
        if not NOTION_TOKEN:
            log.error(_red("NOTION_TOKEN no encontrado. Configura la variable de entorno."))
            db_results = [{"db": k, "status": "skipped"} for k in NOTION_DBS]
        else:
            db_tasks = [check_notion_db(client, name, db_id) for name, db_id in NOTION_DBS.items()]
            db_results = await asyncio.gather(*db_tasks)
            for r in db_results:
                icon = _green("✅") if r["status"] == "ok" else _red("❌")
                latency = f"{r.get('latency_ms', '?')}ms"
                err = f" — {r.get('error', r.get('http', ''))}" if r["status"] != "ok" else ""
                log.info(f"  {icon} Notion DB [{r['db']}] → {r['status'].upper()} ({latency}){err}")

        notion_dbs_ok = sum(1 for r in db_results if r["status"] == "ok")
        log.info(f"  Notion DBs: {notion_dbs_ok}/{len(db_results)} accesibles\n")

        # ── 2. Leer agentes desde Notion ─────────────────────────────────────
        log.info(_cyan("[2/3] Leyendo agentes desde 🤖 Agents DB..."))
        agents = await fetch_agents_from_notion(client)

        if not agents:
            log.warning(_yellow("  No se encontraron agentes en la DB. Asegúrate de que los servicios hayan arrancado al menos una vez."))
            # Usar lista de servicios hardcodeada como fallback
            agents = [
                {"id": "local-1", "name": "Backend",                    "type": "Runtime",  "status": "Activo", "service_url": os.environ.get("BACKEND_URL",           "http://localhost:8000"), "last_run": None, "runs_total": 0, "model": None},
                {"id": "local-2", "name": "Agent Runtime",               "type": "Runtime",  "status": "Activo", "service_url": os.environ.get("AGENT_RUNTIME_URL",    "http://localhost:8001"), "last_run": None, "runs_total": 0, "model": None},
                {"id": "local-3", "name": "ScaleOS Supervisor",          "type": "Supervisor","status": "Activo", "service_url": os.environ.get("SCALEOS_SUPERVISOR_URL","http://localhost:8002"), "last_run": None, "runs_total": 0, "model": None},
                {"id": "local-4", "name": "SEO & OSINT Agent",           "type": "SEO/OSINT","status": "Activo", "service_url": os.environ.get("SEO_OSINT_AGENT_URL",  "http://localhost:8003"), "last_run": None, "runs_total": 0, "model": None},
                {"id": "local-5", "name": "Growth Intelligence Agent",   "type": "Growth",   "status": "Activo", "service_url": os.environ.get("GROWTH_INTELLIGENCE_URL","http://localhost:8004"),"last_run": None, "runs_total": 0, "model": None},
            ]
            log.info(f"  Usando {len(agents)} agentes del fallback local.")
        else:
            log.info(f"  {len(agents)} agentes encontrados en Notion.")

        # ── 3. Health check concurrente de todos los agentes ─────────────────
        log.info(_cyan(f"\n[3/3] Verificando {len(agents)} agentes en paralelo (timeout={timeout}s)...\n"))
        check_tasks = [check_agent_health(client, a, timeout, max_age_hours) for a in agents]
        results = await asyncio.gather(*check_tasks)

        for r in results:
            icon = _green("✅ READY") if r["ready"] else _red("❌ FAIL ")
            issues_str = f" — {'; '.join(r['issues'])}" if r["issues"] else ""
            latency = r.get("checks", {}).get("health_endpoint", {}).get("latency_ms")
            latency_str = f" ({latency}ms)" if latency else ""
            log.info(f"  {icon} | {r['name']:<35} | {r.get('type','?'):<12}{latency_str}{_red(issues_str) if issues_str else ''}")

    # ── Resumen ───────────────────────────────────────────────────────────────
    ready     = [r for r in results if r["ready"]]
    failed    = [r for r in results if not r["ready"]]
    total     = len(results)
    pct_ready = round(len(ready) / total * 100) if total else 0

    log.info("")
    log.info(_bold("=" * 60))
    log.info(_bold("  RESUMEN"))
    log.info(_bold("=" * 60))
    log.info(f"  Total agentes evaluados : {total}")
    log.info(f"  {_green(f'Ready                   : {len(ready)} ({pct_ready}%)')}")
    if failed:
        log.info(f"  {_red(f'Con fallos               : {len(failed)}')}")
        for f in failed:
            log.info(f"    → {f['name']}: {'; '.join(f['issues']) or 'sin issues registradas'}")
    log.info(f"  Notion DBs accesibles   : {notion_dbs_ok}/{len(db_results)}")
    log.info(_bold("=" * 60))

    if pct_ready == 100:
        log.info(_green(_bold("  ✅ TODOS LOS AGENTES ESTÁN READY")))
    elif pct_ready >= 75:
        log.info(_yellow(_bold(f"  ⚠️  SISTEMA PARCIALMENTE OPERATIVO ({pct_ready}%)")))
    else:
        log.error(_red(_bold(f"  ❌ SISTEMA DEGRADADO — solo {pct_ready}% de agentes ready")))
    log.info("")

    return {
        "started_at":      started_at,
        "finished_at":     datetime.utcnow().isoformat(),
        "total_agents":    total,
        "ready":           len(ready),
        "failed":          len(failed),
        "pct_ready":       pct_ready,
        "notion_dbs_ok":   notion_dbs_ok,
        "notion_dbs_total":len(db_results),
        "agents":          results,
        "notion_dbs":      db_results,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Test masivo de agentes — AI Venture Studio OS")
    parser.add_argument("--timeout",       type=float, default=5.0,  help="Timeout por health check (segundos)")
    parser.add_argument("--max-age-hours", type=int,   default=24,   help="Horas máx desde el último run (default 24)")
    parser.add_argument("--report",        type=str,   default="",   help="Ruta para guardar reporte JSON (opcional)")
    args = parser.parse_args()

    report = asyncio.run(run_tests(args.timeout, args.max_age_hours))

    if args.report:
        path = Path(args.report)
        path.write_text(json.dumps(report, indent=2, default=str))
        log.info(f"  Reporte guardado en: {path.resolve()}")

    # Exit code: 0 si todos ready, 1 si alguno falla
    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
