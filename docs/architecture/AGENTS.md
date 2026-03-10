# Agentes — AI Venture Studio OS

## Agent Runtime (`apps/agent_runtime` :8001)

Motor de ejecución de agentes. Recibe una sesión con un bundle de objetivos (DSL JSON) y los ejecuta paso a paso usando el LLM configurado.

**Endpoints:**
- `POST /sessions` — crea y arranca una sesión de agente
- `GET /sessions/{id}` — estado de una sesión
- `DELETE /sessions/{id}` — cancela una sesión

**Mensajes NATS:**
- Publica: `agent.session.started`, `agent.session.completed`, `agent.session.failed`

---

## ScaleOS Supervisor (`apps/scaleos_supervisor` :8002)

Supervisor que monitoriza el progreso de startups hacia sus OKRs y genera recomendaciones tácticas.

**Endpoints:**
- `GET /objectives` — OKRs activos por organización
- `POST /objectives` — crea un objetivo
- `GET /recommendations/{startup_id}` — recomendaciones para una startup

**Mensajes NATS:**
- Suscribe: `agent.session.completed`
- Publica: `supervisor.recommendation.created`

---

## SEO & OSINT Agent (`apps/seo_osint_agent` :8003)

Agente de inteligencia competitiva. Rastrea keywords, SERPs y señales públicas de competidores.

**Endpoints:**
- `POST /opportunities` — lanza análisis OSINT para una startup
- `GET /opportunities/{id}` — resultado del análisis

**Mensajes NATS:**
- Suscribe: `supervisor.recommendation.created` (cuando el supervisor pide análisis)
- Publica: `osint.opportunity.found`

---

## Growth Intelligence Agent (`apps/growth_intelligence_agent` :8004)

Genera briefs de crecimiento accionables basados en datos de la startup y señales del mercado.

**Endpoints:**
- `POST /briefs` — genera un brief de crecimiento
- `GET /briefs/{id}` — recupera un brief

**Mensajes NATS:**
- Suscribe: `osint.opportunity.found`
- Publica: `growth.brief.ready`
