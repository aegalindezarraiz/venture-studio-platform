#!/usr/bin/env bash
# smoke_test.sh — Verifica que todos los servicios responden
set -euo pipefail

BASE_URL="${1:-http://localhost}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local url="$2"
  local expected="${3:-200}"

  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")

  if [ "$status" = "$expected" ]; then
    echo "  ✅ $name ($url) → $status"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $name ($url) → $status (esperado $expected)"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "🔍 Smoke tests — AI Venture Studio OS"
echo "======================================="

check "Backend health"              "$BASE_URL:8000/health"
check "Backend OpenAPI"             "$BASE_URL:8000/docs"
check "Agent Runtime health"        "$BASE_URL:8001/health"
check "ScaleOS Supervisor health"   "$BASE_URL:8002/health"
check "SEO OSINT Agent health"      "$BASE_URL:8003/health"
check "Growth Intelligence health"  "$BASE_URL:8004/health"
check "Frontend"                    "$BASE_URL:5173"
check "Qdrant"                      "$BASE_URL:6333/"
check "NATS Monitor"                "$BASE_URL:8222"

echo ""
echo "Resultado: $PASS OK, $FAIL fallidos"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
