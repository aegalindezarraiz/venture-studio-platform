# Arquitectura — AI Venture Studio OS

## Visión general

Sistema multi-agente para operar una studio de ventures con IA. Cada agente es un microservicio autónomo que se comunica vía NATS JetStream. El backend principal orquesta autenticación, multi-tenancy y persistencia.

## Diagrama de servicios

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                    │
│                   apps/frontend :5173                   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────┐
│               BACKEND (FastAPI) :8000                   │
│   Auth · Multi-tenant · CRUD · Queue dispatch           │
└──┬─────────┬───────────────────────────┬────────────────┘
   │ SQL     │ Redis Queue               │ HTTP
   ▼         ▼                           ▼
┌──────┐  ┌──────┐            ┌──────────────────────────┐
│  PG  │  │ RQ   │            │    NATS JetStream Bus     │
│ :5432│  │Worker│            └──┬──────────┬────────────┘
└──────┘  └──────┘               │          │
                       ┌─────────▼──┐  ┌────▼────────────┐
                       │Agent Runtime│  │ScaleOS Supervisor│
                       │   :8001    │  │     :8002        │
                       └────────────┘  └─────────────────┘
                       ┌─────────────┐ ┌─────────────────┐
                       │SEO/OSINT    │ │Growth Intelligence│
                       │   :8003    │ │     :8004        │
                       └────────────┘ └─────────────────┘
                       ┌─────────────────────────────────┐
                       │        Qdrant :6333             │
                       │    (memoria vectorial)          │
                       └─────────────────────────────────┘
```

## Principios de diseño

1. **Agentes independientes** — cada agente tiene su propio proceso, Dockerfile y ciclo de vida.
2. **Mensajería asíncrona** — NATS JetStream como bus central; ningún agente llama directamente a otro vía HTTP en producción.
3. **Multi-tenancy** — todas las entidades pertenecen a una `Organization`; el backend valida el contexto en cada request.
4. **Memoria durable** — PostgreSQL para estado transaccional, Qdrant para búsqueda semántica.
5. **Observable** — cada servicio expone `/health`, métricas Prometheus y logs estructurados.

## Flujo de un workflow

```
Usuario → POST /workflows → Backend → enqueue(RQ) → Worker
Worker → ejecuta pasos → publica en NATS → Agentes reaccionan
Agentes → escriben resultados → Backend actualiza estado
Backend → Frontend polling / WebSocket → UI actualiza
```
