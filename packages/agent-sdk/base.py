"""
packages/agent-sdk/base.py
══════════════════════════════════════════════════════════════════════════════
NotionAgentBase — ADN de todos los 500 agentes del AI Venture Studio OS.

Responsabilidades automáticas:
  ① Conexión lazy a Notion (solo cuando se necesita, sin fallar en startup)
  ② Auto-registro en la DB 🤖 Agents de Notion al primer run
  ③ Reporte de estado en tiempo real al 🤖 Monitor de Agentes
  ④ Ciclo de vida completo: Idle → Trabajando → Online / Error
  ⑤ Tracking de tokens usados y latencia por ejecución
  ⑥ Llamadas a Claude con conteo automático de tokens

Uso mínimo:
    class MiAgente(NotionAgentBase):
        agent_id    = "growth-seo-001"
        agent_name  = "SEO Analyzer"
        category    = "growth"
        role        = "SEO Specialist"
        model       = "claude-sonnet-4-6"
        priority    = 2
        system_prompt = "Eres un experto en SEO..."

        async def execute(self, ctx: AgentContext) -> AgentResult:
            output = self.call_llm(ctx.payload.get("prompt", ""))
            return AgentResult(task_id=ctx.task_id, agent_id=self.agent_id,
                               status=AgentStatus.SUCCESS, output=output)
══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import abc
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

import anthropic

from packages.agent_sdk.types import AgentContext, AgentResult, AgentStatus

log = logging.getLogger("agent-sdk.base")

# ── Notion DB IDs ─────────────────────────────────────────────────────────────
MONITOR_DB_ID = os.environ.get("NOTION_DB_MONITOR", "1ba923066cec454fbc9320995cfbaf7c")
AGENTS_DB_ID  = os.environ.get("NOTION_DB_AGENTS",  "cf83b9a4254a4140910e1bf50b3fd7d2")

# ── Mapeo de prioridad → etiqueta Notion ──────────────────────────────────────
_PRIORITY_LABELS = {1: "1 - Crítico", 2: "2 - Normal", 3: "3 - Soporte"}

# ── Cache global: agent_name → monitor_page_id  (compartido entre instancias) ─
_monitor_page_cache: dict[str, str] = {}
_agents_page_cache:  dict[str, str] = {}
_cache_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# NotionAgentBase
# ─────────────────────────────────────────────────────────────────────────────

class NotionAgentBase(abc.ABC):
    """
    Clase base con Notion integrado.
    Cada agente hereda de esta clase y sobreescribe los atributos de clase
    y el método `execute()`.
    """

    # ── Atributos de clase — sobreescribir en subclase ─────────────────────────
    agent_id:     str = "base-agent"
    agent_name:   str = "Base Agent"
    category:     str = "engineering"      # executive|product|engineering|growth|data|security|osint
    role:         str = "Generic Agent"
    description:  str = ""
    model:        str = "claude-sonnet-4-6"
    priority:     int = 2                  # 1=crítico 2=normal 3=soporte
    system_prompt: str = (
        "Eres un agente AI especializado del AI Venture Studio OS. "
        "Ejecuta tus tareas con precisión y reporta resultados estructurados."
    )
    max_tokens: int = 2048

    # ── Constructor ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self.log = logging.getLogger(f"agent.{self.agent_id}")
        self._anthropic = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        self._notion: Optional[Any] = None          # lazy — se crea en _get_notion()
        self._notion_available: Optional[bool] = None  # None = no chequeado aún
        self._runs_total: int = 0                   # contador local de runs
        self._tokens_total: int = 0                 # tokens acumulados
        self._registered: bool = False              # ya registrado en 🤖 Agents DB

    # =========================================================================
    # Método abstracto — implementar en cada agente
    # =========================================================================

    @abc.abstractmethod
    async def execute(self, ctx: AgentContext) -> AgentResult:
        """
        Lógica principal del agente.
        Implementar en la subclase. No llamar directamente — usar `run()`.
        """
        ...

    # =========================================================================
    # Ciclo de vida completo — punto de entrada principal
    # =========================================================================

    async def run(self, ctx: AgentContext) -> AgentResult:
        """
        Ejecuta el agente con ciclo de vida completo:
          1. Registra en Notion (primer run)
          2. Marca estado → Trabajando en Monitor
          3. Ejecuta `execute(ctx)`
          4. Marca estado → Online / Error en Monitor
          5. Actualiza métricas (latencia, tokens, runs total)
        """
        start = time.perf_counter()
        self.log.info(f"[{ctx.task_id}] ▶ Iniciando — agent={self.agent_id}")

        # ① Auto-registro en 🤖 Agents DB (una sola vez por instancia)
        if not self._registered:
            self._fire_and_forget(self._register_in_agents_db)

        # ② Marcar como "Trabajando" en el Monitor
        self._fire_and_forget(
            lambda: self.report_to_monitor(
                estado="Trabajando",
                ultima_accion=f"Task {ctx.task_id[:8]} iniciada",
            )
        )

        # ③ Ejecutar lógica principal
        result: AgentResult
        try:
            result = await self.execute(ctx)
            result.duration_ms = round((time.perf_counter() - start) * 1000)
            self._runs_total += 1
            if result.tokens_used:
                self._tokens_total += result.tokens_used
            self.log.info(
                f"[{ctx.task_id}] ✓ Completado en {result.duration_ms}ms "
                f"— status={result.status.value} tokens={result.tokens_used}"
            )
        except Exception as exc:
            ms = round((time.perf_counter() - start) * 1000)
            self.log.error(f"[{ctx.task_id}] ✗ Error en {ms}ms: {exc}")
            result = AgentResult(
                task_id=ctx.task_id,
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error=str(exc),
                duration_ms=ms,
            )

        # ④ Reportar estado final al Monitor (en background)
        _estado = "Online" if result.status == AgentStatus.SUCCESS else "Error"
        _accion = (
            f"Task {ctx.task_id[:8]} completada en {result.duration_ms}ms"
            if result.status == AgentStatus.SUCCESS
            else f"Error: {(result.error or '')[:120]}"
        )
        self._fire_and_forget(
            lambda: self.report_to_monitor(
                estado=_estado,
                ultima_accion=_accion,
                latencia_ms=result.duration_ms,
                runs_total=self._runs_total,
            )
        )

        return result

    # =========================================================================
    # Notion — reporte al Monitor de Agentes
    # =========================================================================

    def report_to_monitor(
        self,
        estado: str = "Online",
        ultima_accion: str = "",
        latencia_ms: Optional[int] = None,
        runs_total: Optional[int] = None,
    ) -> dict:
        """
        Actualiza el estado de este agente en la DB 🤖 Monitor de Agentes.

        Args:
            estado:        "Online" | "Trabajando" | "Error"
            ultima_accion: Texto libre — qué hizo el agente en su última acción.
            latencia_ms:   Latencia de la última ejecución en milisegundos.
            runs_total:    Total de runs completados (usa _runs_total si None).

        Returns:
            dict con action ("created"|"updated") y page_id de Notion.

        El método es seguro para llamar desde cualquier hilo.
        Si Notion no está disponible, loggea una advertencia y retorna vacío.
        """
        notion = self._get_notion()
        if not notion:
            return {}

        now_iso = datetime.now(timezone.utc).isoformat()
        props = {
            "Nombre del Agente": {"title": [{"text": {"content": self.agent_name}}]},
            "Estado":            {"select": {"name": estado}},
            "Categoría":         {"select": {"name": self.category}},
            "Modelo":            {"select": {"name": self.model}},
            "Prioridad":         {"select": {"name": _PRIORITY_LABELS.get(self.priority, "2 - Normal")}},
            "Última Acción":     {"rich_text": [{"text": {"content": ultima_accion[:2000]}}]},
            "Última Actualización": {"date": {"start": now_iso}},
            "Runs Total":        {"number": runs_total if runs_total is not None else self._runs_total},
        }
        if latencia_ms is not None:
            props["Latencia (ms)"] = {"number": latencia_ms}

        try:
            page_id = self._get_monitor_page_id(notion)

            if page_id:
                notion.pages.update(page_id=page_id, properties=props)
                result = {"action": "updated", "page_id": page_id}
            else:
                page = notion.pages.create(
                    parent={"database_id": MONITOR_DB_ID},
                    properties=props,
                )
                page_id = page["id"]
                with _cache_lock:
                    _monitor_page_cache[self.agent_name] = page_id
                result = {"action": "created", "page_id": page_id}

            self.log.debug(f"Monitor updated: action={result['action']} estado={estado}")
            return result

        except Exception as exc:
            self.log.warning(f"report_to_monitor failed: {exc}")
            return {}

    # =========================================================================
    # Notion — registro en 🤖 Agents DB
    # =========================================================================

    def _register_in_agents_db(self) -> None:
        """
        Crea o actualiza la entrada de este agente en la DB 🤖 Agents.
        Se llama automáticamente en el primer `run()`.
        Registra: nombre, tipo (categoría), modelo, URL de servicio.
        """
        notion = self._get_notion()
        if not notion:
            return

        backend_url = os.environ.get("BACKEND_URL", "http://localhost:8020")
        service_url = f"{backend_url}/agents/{self.agent_id}"

        _type_map = {
            "executive": "Supervisor", "product": "Custom",
            "engineering": "Runtime",  "growth": "Growth",
            "data": "Custom",          "security": "Custom",
            "osint": "SEO/OSINT",
        }

        props = {
            "Name":        {"title": [{"text": {"content": f"[{self.category.upper()}] {self.role}"}}]},
            "Type":        {"select": {"name": _type_map.get(self.category, "Custom")}},
            "Model":       {"select": {"name": self.model}},
            "Service URL": {"url": service_url},
        }

        try:
            page_id = self._get_agents_page_id(notion)
            if page_id:
                notion.pages.update(page_id=page_id, properties=props)
            else:
                page = notion.pages.create(
                    parent={"database_id": AGENTS_DB_ID},
                    properties=props,
                )
                with _cache_lock:
                    _agents_page_cache[self.agent_id] = page["id"]

            self._registered = True
            self.log.debug(f"Registered in Agents DB: {self.agent_id}")

        except Exception as exc:
            self.log.warning(f"_register_in_agents_db failed: {exc}")

    # =========================================================================
    # LLM — llamada a Claude con tracking de tokens
    # =========================================================================

    def call_llm(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> str:
        """
        Llama a Claude y retorna el texto de respuesta.
        Acumula tokens en `self._tokens_total` para métricas.

        Args:
            prompt:      Mensaje del usuario.
            system:      System prompt (usa self.system_prompt si None).
            max_tokens:  Máx. tokens de respuesta (usa self.max_tokens si None).
            temperature: Temperatura de sampling (1.0 = default Claude).

        Returns:
            Texto de la respuesta del modelo.
        """
        response = self._anthropic.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            system=system or self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        tokens = response.usage.output_tokens
        self._tokens_total += tokens
        self.log.debug(f"LLM call: {tokens} output tokens (total={self._tokens_total})")
        return response.content[0].text

    def call_llm_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Llama a Claude en modo streaming.
        Retorna el stream object de Anthropic (usar con `with` o iterador).

        Ejemplo:
            with agent.call_llm_stream("Resume esto: ...") as stream:
                for chunk in stream.text_stream:
                    print(chunk, end="", flush=True)
        """
        return self._anthropic.messages.stream(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            system=system or self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )

    def call_llm_with_tools(
        self,
        prompt: str,
        tools: list[dict],
        system: Optional[str] = None,
    ) -> Any:
        """
        Llama a Claude con herramientas (tool use / function calling).

        Args:
            prompt: Mensaje del usuario.
            tools:  Lista de tool definitions en formato Anthropic.
            system: System prompt opcional.

        Returns:
            Objeto de respuesta completo de Anthropic (para procesar tool_use blocks).
        """
        return self._anthropic.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system or self.system_prompt,
            tools=tools,
            messages=[{"role": "user", "content": prompt}],
        )

    # =========================================================================
    # Métricas locales
    # =========================================================================

    @property
    def stats(self) -> dict:
        """Métricas acumuladas de esta instancia del agente."""
        return {
            "agent_id":     self.agent_id,
            "agent_name":   self.agent_name,
            "category":     self.category,
            "model":        self.model,
            "priority":     self.priority,
            "runs_total":   self._runs_total,
            "tokens_total": self._tokens_total,
            "registered":   self._registered,
            "notion_ok":    self._notion_available,
        }

    # =========================================================================
    # Internals
    # =========================================================================

    def _get_notion(self) -> Optional[Any]:
        """
        Retorna el cliente de Notion, creándolo la primera vez.
        Si NOTION_TOKEN no está configurado, o hay error de conexión,
        marca `_notion_available = False` y retorna None.
        El agente sigue funcionando aunque Notion no esté disponible.
        """
        if self._notion_available is False:
            return None
        if self._notion is not None:
            return self._notion

        token = os.environ.get("NOTION_TOKEN")
        if not token:
            self.log.warning(
                f"[{self.agent_id}] NOTION_TOKEN no configurado — "
                "funcionando sin sincronización a Notion."
            )
            self._notion_available = False
            return None

        try:
            from notion_client import Client
            self._notion = Client(auth=token)
            self._notion_available = True
            self.log.debug(f"[{self.agent_id}] Notion client inicializado.")
            return self._notion
        except ImportError:
            self.log.warning(
                f"[{self.agent_id}] notion-client no instalado — "
                "pip install notion-client"
            )
            self._notion_available = False
            return None
        except Exception as exc:
            self.log.warning(f"[{self.agent_id}] Notion init error: {exc}")
            self._notion_available = False
            return None

    def _get_monitor_page_id(self, notion) -> Optional[str]:
        """
        Busca el page_id del Monitor de Agentes para este agente.
        Usa cache global para evitar N+1 queries.
        """
        with _cache_lock:
            if self.agent_name in _monitor_page_cache:
                return _monitor_page_cache[self.agent_name]

        # No estaba en cache — buscar en Notion
        try:
            r = notion.databases.query(
                database_id=MONITOR_DB_ID,
                filter={"property": "Nombre del Agente", "title": {"equals": self.agent_name}},
                page_size=1,
            )
            pages = r.get("results", [])
            if pages:
                page_id = pages[0]["id"]
                with _cache_lock:
                    _monitor_page_cache[self.agent_name] = page_id
                return page_id
        except Exception as exc:
            self.log.debug(f"_get_monitor_page_id query failed: {exc}")

        return None

    def _get_agents_page_id(self, notion) -> Optional[str]:
        """
        Busca el page_id en la DB 🤖 Agents para este agente.
        Usa cache global.
        """
        with _cache_lock:
            if self.agent_id in _agents_page_cache:
                return _agents_page_cache[self.agent_id]

        try:
            # En la Agents DB el nombre tiene formato [CATEGORY] role
            search_name = f"[{self.category.upper()}] {self.role}"
            r = notion.databases.query(
                database_id=AGENTS_DB_ID,
                filter={"property": "Name", "title": {"equals": search_name}},
                page_size=1,
            )
            pages = r.get("results", [])
            if pages:
                page_id = pages[0]["id"]
                with _cache_lock:
                    _agents_page_cache[self.agent_id] = page_id
                return page_id
        except Exception as exc:
            self.log.debug(f"_get_agents_page_id query failed: {exc}")

        return None

    def _fire_and_forget(self, fn) -> None:
        """
        Ejecuta `fn` en un hilo daemon sin bloquear el event loop principal.
        Usado para reportes a Notion que no deben ralentizar la ejecución del agente.
        """
        t = threading.Thread(target=fn, daemon=True)
        t.start()

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"id={self.agent_id!r} "
            f"category={self.category!r} "
            f"runs={self._runs_total}>"
        )
