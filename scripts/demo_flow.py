"""
demo_flow.py — Demostración end-to-end del AI Venture Studio OS.

Ejecuta el flujo completo:
  1. Crea una startup en Notion
  2. Crea un OKR para esa startup
  3. Genera un Brief de crecimiento (Growth Agent → Notion)
  4. Lanza análisis SEO/OSINT (OSINT Agent → Notion)
  5. Genera recomendaciones del Supervisor (ScaleOS → Notion)
  6. Genera Weekly Review automática

Uso:
  python scripts/demo_flow.py [--backend http://tu-dominio.railway.app]
"""
import argparse
import sys
import time
import httpx

DEFAULT_BACKEND = "http://localhost:8000"
DEFAULT_GROWTH  = "http://localhost:8004"
DEFAULT_OSINT   = "http://localhost:8003"
DEFAULT_SUPER   = "http://localhost:8002"


def ok(msg: str): print(f"  ✅ {msg}")
def info(msg: str): print(f"  ℹ  {msg}")
def fail(msg: str): print(f"  ❌ {msg}")
def section(title: str): print(f"\n{'═'*55}\n  {title}\n{'═'*55}")


def post(base: str, path: str, payload: dict, label: str) -> dict | None:
    try:
        r = httpx.post(f"{base}{path}", json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        ok(f"{label} → {data.get('id', data.get('name', 'OK'))}")
        return data
    except Exception as e:
        fail(f"{label}: {e}")
        return None


def get(base: str, path: str, params: dict = {}) -> dict:
    try:
        r = httpx.get(f"{base}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        fail(f"GET {path}: {e}")
        return {}


def run(backend: str, growth: str, osint: str, supervisor: str):

    # ── 0. Health checks ──────────────────────────────────────────────────────
    section("0 · Health checks")
    for name, url in [("Backend", backend), ("Growth", growth), ("OSINT", osint), ("Supervisor", supervisor)]:
        try:
            r = httpx.get(f"{url}/health", timeout=5)
            ok(f"{name} → {r.json().get('status','?')}")
        except Exception as e:
            fail(f"{name} no responde: {e}")

    # ── 1. Crear startup en Notion ─────────────────────────────────────────────
    section("1 · Crear startup en Notion")
    startup = post(backend, "/notion/startups", {}, "Startup")
    # La API de startups es solo lectura (Notion como source of truth).
    # Usamos una startup existente o la primera disponible.
    startups = get(backend, "/notion/startups", {"status": "Activa"}).get("startups", [])
    if not startups:
        fail("No hay startups activas en Notion. Crea una desde Notion primero.")
        return
    startup = startups[0]
    startup_id = startup["id"]
    startup_name = startup["name"]
    ok(f"Usando startup: '{startup_name}' ({startup_id[:8]}...)")

    # ── 2. Crear OKR ──────────────────────────────────────────────────────────
    section("2 · Crear OKR en Notion")
    okr = post(backend, "/notion/okrs", {
        "name": "Alcanzar $10k MRR",
        "startup_id": startup_id,
        "quarter": "Q2-2026",
        "type": "Objetivo",
    }, "OKR")

    # ── 3. Growth Brief ───────────────────────────────────────────────────────
    section("3 · Generar Growth Brief (Growth Intelligence Agent)")
    brief_resp = post(growth, "/briefs", {
        "startup_id": startup_id,
        "startup_name": startup_name,
        "stage": startup.get("stage", "MVP"),
        "industry": "SaaS",
        "current_metrics": {"mrr": startup.get("mrr") or 0, "churn": 5},
        "goals": ["Crecer MRR 3x en 90 días", "Reducir churn a <3%"],
    }, "Brief generado")

    if brief_resp:
        notion_brief_id = brief_resp.get("notion_brief_id")
        info(f"Brief en Notion: {notion_brief_id or 'sincronizando...'}")
        content_preview = brief_resp.get("content", "")[:120].replace("\n", " ")
        info(f"Preview: {content_preview}...")

    # ── 4. SEO/OSINT Analysis ─────────────────────────────────────────────────
    section("4 · Análisis SEO/OSINT")
    opp = post(osint, "/opportunities", {
        "startup_id": startup_id,
        "startup_name": startup_name,
        "domain": "mi-startup.com",
        "keywords": ["automatización empresarial", "agentes ia latam", "rpa pymes"],
        "competitors": ["rocketbot.com", "uipath.com"],
    }, "Análisis lanzado")

    if opp:
        info("Análisis corriendo en background → creando experiments en Notion...")
        time.sleep(3)
        opp_status = get(osint, f"/opportunities/{opp['id']}")
        info(f"Estado: {opp_status.get('status')} — Experiments creados: {opp_status.get('experiments_created', 0)}")

    # ── 5. Recomendaciones del Supervisor ─────────────────────────────────────
    section("5 · Recomendaciones tácticas (ScaleOS Supervisor)")
    recs = post(supervisor, "/recommendations", {
        "startup_id": startup_id,
        "startup_name": startup_name,
        "stage": startup.get("stage", "MVP"),
        "industry": "SaaS",
        "mrr": startup.get("mrr") or 0,
        "at_risk_okrs": [],
    }, "Recomendaciones generadas")

    if recs:
        for i, rec in enumerate(recs.get("recommendations", []), 1):
            info(f"  {i}. {rec}")

    # ── 6. Weekly Review ──────────────────────────────────────────────────────
    section("6 · Weekly Review automática (ScaleOS Monitor)")
    review = post(supervisor, "/monitor/weekly", {}, "Weekly Review")
    if review:
        info(f"Health Score del Studio: {review.get('health_score')} / 100")
        info(f"OKRs en riesgo detectados: {review.get('okrs_at_risk')}")
        if review.get("notion_url"):
            info(f"Ver en Notion: {review['notion_url']}")

    # ── Resumen ───────────────────────────────────────────────────────────────
    section("Resumen del flujo")
    print(f"""
  Startup:    {startup_name}
  OKR:        Alcanzar $10k MRR (Q2-2026)
  Brief:      {'✅ Generado y en Notion' if brief_resp else '❌ Falló'}
  SEO/OSINT:  {'✅ Análisis corriendo' if opp else '❌ Falló'}
  Supervisor: {'✅ Recomendaciones creadas en Notion' if recs else '❌ Falló'}
  Review:     {'✅ Weekly Review en Notion' if review else '❌ Falló'}

  Revisa tu Notion para ver todos los registros creados automáticamente.
    """)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo flow — AI Venture Studio OS")
    parser.add_argument("--backend",    default=DEFAULT_BACKEND)
    parser.add_argument("--growth",     default=DEFAULT_GROWTH)
    parser.add_argument("--osint",      default=DEFAULT_OSINT)
    parser.add_argument("--supervisor", default=DEFAULT_SUPER)
    args = parser.parse_args()

    run(
        backend=args.backend,
        growth=args.growth,
        osint=args.osint,
        supervisor=args.supervisor,
    )
