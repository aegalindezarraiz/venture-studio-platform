"""
example_agent.py — Ejemplo de implementación usando NotionAgentBase.

Demuestra cómo crear cualquiera de los 500 agentes del Venture Studio OS
con reporte automático al Monitor de Agentes en Notion.

Ejecutar:
    python -m packages.agent_sdk.example_agent
"""

import asyncio
import os
import uuid

from packages.agent_sdk.base import NotionAgentBase
from packages.agent_sdk.types import AgentContext, AgentResult, AgentStatus


# ─────────────────────────────────────────────────────────────────────────────
# Ejemplo 1: SEO Analyzer (Growth category)
# ─────────────────────────────────────────────────────────────────────────────

class SEOAnalyzerAgent(NotionAgentBase):
    """
    Analiza keywords y genera estrategias SEO.
    Categoría: growth | Prioridad: 2 - Normal
    """

    # ── Identidad del agente — esto es lo que aparece en el Monitor de Notion ──
    agent_id    = "growth-seo-001"
    agent_name  = "SEO Analyzer"
    category    = "growth"
    role        = "SEO Specialist"
    description = "Analiza keywords, competidores y genera estrategias SEO accionables."
    model       = "claude-sonnet-4-6"
    priority    = 2

    system_prompt = """Eres un experto en SEO con 10 años de experiencia.
Analizas keywords, competidores y arquitectura de sitios web.
Tus recomendaciones son específicas, priorizadas y basadas en datos.
Responde siempre en formato JSON estructurado."""

    async def execute(self, ctx: AgentContext) -> AgentResult:
        """Analiza las keywords del payload y devuelve estrategia SEO."""
        keywords = ctx.payload.get("keywords", [])
        domain   = ctx.payload.get("domain", "mi-startup.com")

        if not keywords:
            return AgentResult(
                task_id=ctx.task_id,
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error="keywords requeridas en payload",
            )

        prompt = f"""Analiza las siguientes keywords para el dominio {domain}:
Keywords: {", ".join(keywords)}

Genera:
1. Dificultad estimada por keyword (low/medium/high)
2. Volumen de búsqueda estimado
3. Intención de búsqueda (informacional/transaccional/navegacional)
4. Top 3 páginas de contenido a crear
5. Estrategia de link building (3 tácticas)
6. Quick wins para los próximos 30 días

JSON estructurado."""

        output = self.call_llm(prompt)

        return AgentResult(
            task_id=ctx.task_id,
            agent_id=self.agent_id,
            status=AgentStatus.SUCCESS,
            output=output,
            tokens_used=len(output.split()) * 2,   # estimación
            metadata={"keywords": keywords, "domain": domain},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Ejemplo 2: Due Diligence Agent (Executive category, Prioridad 1)
# ─────────────────────────────────────────────────────────────────────────────

class DueDiligenceAgent(NotionAgentBase):
    """
    Ejecuta análisis de due diligence de startups para el portfolio.
    Categoría: executive | Prioridad: 1 - Crítico
    """

    agent_id    = "exec-dd-001"
    agent_name  = "Due Diligence Analyst"
    category    = "executive"
    role        = "Investment Analyst"
    description = "Due diligence de startups: viabilidad, riesgos, recomendación de inversión."
    model       = "claude-opus-4-6"          # Opus para decisiones críticas
    priority    = 1                          # 1 = Crítico

    system_prompt = """Eres un analista de inversiones senior de un venture studio.
Tu análisis es riguroso, basado en primeros principios y siempre incluye
una recomendación clara: INVEST / PASS / NEGOTIATE.
Hablas con la precisión de un CFO y la visión de un fundador."""

    async def execute(self, ctx: AgentContext) -> AgentResult:
        startup = ctx.payload.get("startup_name", "Startup")
        sector  = ctx.payload.get("sector", "tech")
        stage   = ctx.payload.get("stage", "seed")
        amount  = ctx.payload.get("investment_usd", 100_000)
        desc    = ctx.payload.get("description", "")

        prompt = f"""Due diligence para potencial inversión:
Startup: {startup} | Sector: {sector} | Etapa: {stage}
Inversión solicitada: ${amount:,} USD
Descripción: {desc}

Evalúa:
1. Score de viabilidad (1-10) con justificación
2. Top 5 riesgos con impacto (alto/medio/bajo)
3. Fortalezas clave del negocio
4. Análisis de mercado (TAM estimado, timing, competencia)
5. Estructura de deal recomendada (equity %, valoración)
6. Hitos de seguimiento post-inversión (3-6 meses)
7. RECOMENDACIÓN FINAL: INVEST / PASS / NEGOTIATE

JSON estructurado."""

        output = self.call_llm(prompt)

        return AgentResult(
            task_id=ctx.task_id,
            agent_id=self.agent_id,
            status=AgentStatus.SUCCESS,
            output=output,
            metadata={"startup": startup, "amount_usd": amount},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Runner de demostración
# ─────────────────────────────────────────────────────────────────────────────

async def demo():
    print("\n" + "═" * 60)
    print("  AI Venture Studio OS — Agent SDK Demo")
    print("═" * 60)

    # ── Demo 1: SEO Analyzer ─────────────────────────────────────────────────
    print("\n[1/2] SEO Analyzer Agent")
    print("─" * 40)

    seo = SEOAnalyzerAgent()
    print(f"  Agent : {seo}")
    print(f"  Model : {seo.model}")
    print(f"  Notion: {'✓ disponible' if os.environ.get('NOTION_TOKEN') else '✗ no configurado (NOTION_TOKEN)'}")

    ctx_seo = AgentContext(
        task_id=str(uuid.uuid4()),
        agent_id=seo.agent_id,
        org_id="org_venture_studio",
        payload={
            "keywords": ["venture studio", "startup generator", "AI startup"],
            "domain": "venture-studio.ai",
        },
    )

    if os.environ.get("ANTHROPIC_API_KEY"):
        result_seo = await seo.run(ctx_seo)
        print(f"  Status: {result_seo.status.value}")
        print(f"  Duration: {result_seo.duration_ms}ms")
        print(f"  Stats: {seo.stats}")
    else:
        print("  ⚠ ANTHROPIC_API_KEY no configurado — demo sin LLM")

    # ── Demo 2: report_to_monitor directo ────────────────────────────────────
    print("\n[2/2] Report directo al Monitor de Agentes")
    print("─" * 40)

    dd = DueDiligenceAgent()
    print(f"  Agent : {dd}")

    # Llamada directa al método de reporte (sin ejecutar el agente)
    result = dd.report_to_monitor(
        estado="Online",
        ultima_accion="Inicializado y listo para análisis de due diligence",
        latencia_ms=0,
        runs_total=0,
    )
    if result:
        print(f"  Monitor: {result}")
    else:
        print("  Monitor: no actualizado (Notion no configurado o error)")

    print("\n" + "═" * 60)
    print("  Instrucciones de uso:")
    print("  1. class MiAgente(NotionAgentBase): → define atributos")
    print("  2. async def execute(self, ctx): → implementa lógica")
    print("  3. await agente.run(ctx) → Notion se actualiza solo")
    print("  4. agente.stats → métricas de la instancia")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
