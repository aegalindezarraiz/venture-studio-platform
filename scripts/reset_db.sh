#!/usr/bin/env bash
# reset_db.sh — Elimina y recrea la base de datos (SOLO DEV)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

read -p "⚠️  Esto borrará TODOS los datos. ¿Continuar? [y/N] " confirm
[ "$confirm" = "y" ] || { echo "Cancelado."; exit 0; }

echo "🗑️  Bajando y eliminando volumen de postgres..."
docker compose -f "$ROOT/docker-compose.yml" down postgres -v
docker compose -f "$ROOT/docker-compose.yml" up -d postgres
sleep 5

echo "🗄️  Re-ejecutando migraciones..."
docker compose -f "$ROOT/docker-compose.yml" run --rm backend alembic upgrade head

echo "🌱 Re-seeding..."
bash "$ROOT/scripts/seed.sh"

echo "✅ Base de datos reiniciada"
