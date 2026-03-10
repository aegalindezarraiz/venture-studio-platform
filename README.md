# AI Venture Studio OS

Monorepo multi-agente para operar una studio de ventures con IA. Incluye backend principal, sistema de agentes autónomos, frontend operativo, infraestructura local completa y despliegue en Kubernetes.

## Estructura

```
AI VENTURE STUDIO OS/
├── apps/
│   ├── backend/                  FastAPI · Auth · Multi-tenant · CRUD · :8000
│   ├── frontend/                 React + TypeScript + Vite · :5173
│   ├── worker/                   RQ worker para jobs asíncronos
│   ├── agent_runtime/            Motor de ejecución de agentes (LLM) · :8001
│   ├── scaleos_supervisor/       Supervisor de OKRs y recomendaciones · :8002
│   ├── seo_osint_agent/          Inteligencia competitiva y SEO · :8003
│   └── growth_intelligence_agent/Briefs de crecimiento con IA · :8004
│
├── packages/
│   ├── shared-py/                Librería Python compartida (bus, db, models, utils)
│   ├── shared-ui/                Componentes React compartidos (Badge, Spinner, useApi…)
│   └── config/                   Configuración central (LLM, entornos)
│
├── infra/
│   ├── postgres/                 init.sql con extensiones
│   ├── redis/                    redis.conf
│   ├── qdrant/                   (configuración Qdrant)
│   └── nats/                     nats.conf con JetStream
│
├── deploy/
│   ├── local/                    docker-compose.override.yml para dev
│   └── k8s/
│       ├── base/                 Manifiestos Kubernetes base
│       └── overlays/
│           ├── staging/          Kustomize overlay staging (1 réplica)
│           └── production/       Kustomize overlay prod (3 réplicas)
│
├── docs/
│   ├── architecture/             OVERVIEW.md · AGENTS.md
│   ├── api/                      ENDPOINTS.md
│   └── runbooks/                 LOCAL_SETUP.md
│
├── scripts/
│   ├── bootstrap.sh              Arranque completo desde cero
│   ├── smoke_test.sh             Verificación de todos los servicios
│   ├── seed.sh                   Carga datos demo
│   └── reset_db.sh               Reset total de DB (solo dev)
│
├── .github/workflows/ci.yml      CI: lint · test · docker build
├── docker-compose.yml            Orquestación local completa
├── .env.example                  Variables de entorno documentadas
└── Makefile                      Comandos abreviados
```

## Inicio rápido

```bash
bash scripts/bootstrap.sh
```

## Servicios

| Servicio                | Puerto | Descripción                        |
|-------------------------|--------|------------------------------------|
| Frontend                | 5173   | React UI operativa                 |
| Backend API             | 8000   | FastAPI + JWT + multi-tenant       |
| Agent Runtime           | 8001   | Motor de ejecución LLM             |
| ScaleOS Supervisor      | 8002   | Supervisor de OKRs                 |
| SEO/OSINT Agent         | 8003   | Inteligencia competitiva           |
| Growth Intelligence     | 8004   | Briefs de crecimiento con IA       |
| PostgreSQL              | 5432   | Base de datos principal            |
| Redis                   | 6379   | Cola de jobs                       |
| Qdrant                  | 6333   | Memoria vectorial                  |
| NATS                    | 4222   | Bus de mensajes entre agentes      |

## Comandos frecuentes

```bash
make up       # Levantar todo
make down     # Bajar todo
make logs     # Ver logs
make migrate  # Aplicar migraciones
make test     # Tests
make smoke    # Smoke tests
make clean    # Reset total
```

## Documentación

- `docs/architecture/OVERVIEW.md` — Arquitectura y diagrama de servicios
- `docs/architecture/AGENTS.md` — Detalle de cada agente
- `docs/api/ENDPOINTS.md` — Referencia de endpoints
- `docs/runbooks/LOCAL_SETUP.md` — Setup local detallado
