# Runbook — Arranque local

## Requisitos

- Docker Desktop >= 4.28
- Docker Compose v2
- Node.js >= 20 (solo si corres el frontend fuera de Docker)
- Python 3.11+ (solo si corres el backend fuera de Docker)

## Inicio rápido (recomendado)

```bash
bash scripts/bootstrap.sh
```

Esto copia `.env`, levanta la infra, migra la DB, crea los streams NATS y levanta todos los servicios.

## Inicio manual paso a paso

```bash
# 1. Variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 2. Infra base
docker compose up -d postgres redis qdrant nats
sleep 5

# 3. Migraciones
docker compose run --rm backend alembic upgrade head

# 4. Todos los servicios
docker compose up -d

# 5. Verificar
bash scripts/smoke_test.sh
```

## URLs de desarrollo

| Servicio              | URL                                |
|-----------------------|------------------------------------|
| Frontend              | http://localhost:5173              |
| Backend API           | http://localhost:8000              |
| OpenAPI Docs          | http://localhost:8000/docs         |
| Agent Runtime         | http://localhost:8001              |
| ScaleOS Supervisor    | http://localhost:8002              |
| SEO/OSINT Agent       | http://localhost:8003              |
| Growth Intelligence   | http://localhost:8004              |
| Qdrant Dashboard      | http://localhost:6333/dashboard    |
| NATS Monitor          | http://localhost:8222              |

## Comandos frecuentes

```bash
make logs       # Ver todos los logs
make migrate    # Aplicar migraciones pendientes
make seed       # Cargar datos demo
make test       # Correr tests
make smoke      # Smoke tests
make clean      # Borrar todo y empezar de cero
```

## Solución de problemas

**Puerto ocupado:**
```bash
docker compose down
lsof -ti:5432 | xargs kill -9   # liberar puerto postgres
```

**Migraciones fallidas:**
```bash
docker compose run --rm backend alembic downgrade base
docker compose run --rm backend alembic upgrade head
```

**Reset total:**
```bash
make clean
bash scripts/bootstrap.sh
```
