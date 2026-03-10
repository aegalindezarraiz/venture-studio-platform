#!/usr/bin/env bash
# seed.sh — Inserta datos de demo en la base de datos
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🌱 Seeding demo data..."
docker compose -f "$ROOT/docker-compose.yml" exec backend python -c "
from app.scripts.seed import run_seed
import asyncio
asyncio.run(run_seed())
"
echo "✅ Seed completo"
