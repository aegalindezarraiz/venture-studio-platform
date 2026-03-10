#!/usr/bin/env bash
# bootstrap.sh — Levanta el entorno completo desde cero
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "▶  AI Venture Studio OS — Bootstrap"
echo "======================================"

# 1. Variables de entorno
if [ ! -f "$ROOT/.env" ]; then
  echo "📋 Copiando .env.example → .env"
  cp "$ROOT/.env.example" "$ROOT/.env"
fi

# 2. Servicios de infra
echo "🐳 Levantando postgres, redis, qdrant, nats..."
docker compose -f "$ROOT/docker-compose.yml" up -d postgres redis qdrant nats
sleep 5

# 3. Migraciones
echo "🗄️  Ejecutando migraciones Alembic..."
docker compose -f "$ROOT/docker-compose.yml" run --rm backend alembic upgrade head

# 4. NATS Streams
echo "📨 Creando NATS JetStream streams..."
docker compose -f "$ROOT/docker-compose.yml" exec nats \
  nats stream add AGENT_EVENTS \
    --subjects "agent.>" \
    --storage file \
    --retention limits \
    --max-msgs -1 \
    --max-bytes -1 \
    --max-age 24h \
    --replicas 1 \
    --defaults 2>/dev/null || true

# 5. Seed de datos demo
echo "🌱 Cargando datos de demo..."
docker compose -f "$ROOT/docker-compose.yml" run --rm backend python -m app.scripts.seed 2>/dev/null || echo "  (seed omitido — sin módulo seed aún)"

# 6. Todos los servicios
echo "🚀 Levantando todos los servicios..."
docker compose -f "$ROOT/docker-compose.yml" up -d

echo ""
echo "✅ Bootstrap completo"
echo "   Frontend  → http://localhost:5173"
echo "   Backend   → http://localhost:8000"
echo "   OpenAPI   → http://localhost:8000/docs"
echo "   Qdrant    → http://localhost:6333/dashboard"
echo "   NATS Mon  → http://localhost:8222"
