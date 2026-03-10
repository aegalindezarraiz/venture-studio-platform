#!/usr/bin/env python3
"""
seed_agents.py — CLI para registrar los 500 agentes en la DB 🤖 Agents de Notion.

Uso:
    python scripts/seed_agents.py
    python scripts/seed_agents.py --batch-size 5 --dry-run
    python scripts/seed_agents.py --category executive
    python scripts/seed_agents.py --summary

Variables de entorno necesarias:
    BACKEND_URL     URL del backend (default: http://localhost:8000)
    NOTION_TOKEN    Token de integración de Notion
"""
import argparse
import os
import sys
import time

# Añadir raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from packages.agents.definitions import ALL_AGENTS, AGENTS_BY_CATEGORY
from packages.agents.registry import get_summary


# ── Colores ANSI ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ok   = lambda s: f"{GREEN}✅ {s}{RESET}"
fail = lambda s: f"{RED}❌ {s}{RESET}"
info = lambda s: f"{CYAN}ℹ  {s}{RESET}"
warn = lambda s: f"{YELLOW}⚠  {s}{RESET}"


def print_summary():
    """Imprime estadísticas del catálogo local (sin Notion)."""
    summary = get_summary()
    print(f"\n{BOLD}=== Catálogo de Agentes AI — Resumen ==={RESET}")
    print(f"Total agentes : {BOLD}{summary['total_agents']}{RESET}")
    print(f"Ready (RT)    : {summary['total_ready']} / {summary['total_checked']} chequeados\n")

    for cat, data in summary["categories"].items():
        bar_len = int((data["total"] / summary["total_agents"]) * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        print(f"  {cat:<12} [{bar}] {data['total']:>3} agentes  (P1: {data['priority_1']})")

    print()


def seed_via_api(batch_size: int, category: str | None, dry_run: bool):
    """Llama al endpoint POST /agents/seed/notion del backend."""
    import httpx

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    url = f"{backend_url}/agents/seed/notion?batch_size={batch_size}"

    agents_to_process = ALL_AGENTS
    if category:
        agents_to_process = AGENTS_BY_CATEGORY.get(category.lower(), [])
        if not agents_to_process:
            print(fail(f"Categoría '{category}' no existe. Opciones: {', '.join(AGENTS_BY_CATEGORY.keys())}"))
            sys.exit(1)

    print(info(f"Agentes a registrar: {len(agents_to_process)}"))
    if dry_run:
        print(warn("Modo DRY-RUN activo — no se realizarán cambios en Notion"))
        for i, a in enumerate(agents_to_process[:5], 1):
            print(f"  [{i}] {a.id:<40} {a.name}")
        if len(agents_to_process) > 5:
            print(f"  ... y {len(agents_to_process) - 5} más")
        print(ok("Dry-run completado"))
        return

    print(info(f"Conectando a backend: {backend_url}"))
    try:
        with httpx.Client(timeout=300) as client:
            t0 = time.perf_counter()
            r = client.post(url)
            elapsed = round(time.perf_counter() - t0, 1)

        if r.status_code == 200:
            data = r.json()
            print(ok(f"Seed completado en {elapsed}s"))
            print(f"  Creados  : {data.get('created', 0)}")
            print(f"  Actualizados: {data.get('updated', 0)}")
            print(f"  Errores  : {data.get('errors', 0)}")
            print(f"  Total    : {data.get('total', 0)}")
        else:
            print(fail(f"El backend respondió {r.status_code}: {r.text[:200]}"))
            sys.exit(1)
    except Exception as e:
        print(fail(f"No se pudo conectar al backend: {e}"))
        print(info("Verifica que el backend esté corriendo en " + backend_url))
        sys.exit(1)


def seed_direct(batch_size: int, category: str | None, dry_run: bool):
    """Seed directo vía registry (sin backend HTTP, requiere NOTION_TOKEN)."""
    from packages.agents.registry import seed_to_notion

    agents_to_process = ALL_AGENTS
    if category:
        from packages.agents.definitions import AGENTS_BY_CATEGORY
        agents_to_process = AGENTS_BY_CATEGORY.get(category.lower(), [])

    if dry_run:
        print(warn("Modo DRY-RUN activo — no se realizarán cambios en Notion"))
        for i, a in enumerate(agents_to_process[:10], 1):
            print(f"  [{i}] {a.id:<40} {a.name}")
        print(ok(f"Dry-run: {len(agents_to_process)} agentes en cola"))
        return

    print(info(f"Seed directo de {len(agents_to_process)} agentes a Notion..."))
    t0 = time.perf_counter()
    result = seed_to_notion(batch_size=batch_size)
    elapsed = round(time.perf_counter() - t0, 1)

    print(ok(f"Seed completado en {elapsed}s"))
    print(f"  Creados     : {result['created']}")
    print(f"  Actualizados: {result['updated']}")
    print(f"  Errores     : {result['errors']}")
    print(f"  Total       : {result['total']}")


def main():
    parser = argparse.ArgumentParser(
        description="Seed de los 500 agentes AI hacia la DB de Notion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--summary",     action="store_true", help="Solo mostrar estadísticas del catálogo local")
    parser.add_argument("--dry-run",     action="store_true", help="Simular sin modificar Notion")
    parser.add_argument("--batch-size",  type=int, default=10, help="Agentes por batch (default: 10)")
    parser.add_argument("--category",   type=str, default=None, help="Filtrar por categoría")
    parser.add_argument("--direct",     action="store_true", help="Seed directo (requiere NOTION_TOKEN)")
    args = parser.parse_args()

    print(f"\n{BOLD}AI Venture Studio OS — Agent Seeder{RESET}")
    print("─" * 40)

    if args.summary:
        print_summary()
        return

    print_summary()

    if args.direct:
        seed_direct(args.batch_size, args.category, args.dry_run)
    else:
        seed_via_api(args.batch_size, args.category, args.dry_run)


if __name__ == "__main__":
    main()
