# Repository Map

## Root
- `.env.example`: variables de entorno base.
- `docker-compose.yml`: orquestación local completa.
- `Makefile`: comandos rápidos.
- `README.md`: guía raíz.

## apps/backend
API FastAPI con autenticación JWT, ORM SQLAlchemy, Alembic, Redis Queue y Qdrant.

### backend/app/api/routes
- `health.py`: healthcheck.
- `auth.py`: registro y login.
- `organizations.py`: multi-tenant base.
- `startups.py`: CRUD de startups.
- `agents.py`: CRUD de agentes.
- `prompts.py`: CRUD de prompts.
- `workflows.py`: cola de workflows.
- `memory.py`: memoria durable + vectorial.

## apps/frontend
Panel React + TypeScript + Vite con login, organización activa y vistas CRUD operativas.

## apps/worker
Worker RQ que procesa workflows y persiste resultados en Postgres + Qdrant.

## infra/postgres
- `init.sql`: extensión UUID.

## k8s/base
Manifiestos base para namespace, postgres, redis, qdrant, backend, worker y frontend.
