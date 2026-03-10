"""Motor de ejecución de agentes con LLM y sincronización a Notion."""
import asyncio
import os
import uuid
from dataclasses import dataclass

import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6")


@dataclass
class Session:
    id: str
    agent_id: str
    status: str   # pending | running | completed | failed | cancelled
    objective_bundle: dict
    context: dict
    result: dict | None = None


class RuntimeService:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._client: anthropic.AsyncAnthropic | None = None

    async def startup(self):
        if ANTHROPIC_API_KEY:
            self._client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    async def shutdown(self):
        pass

    async def create_session(self, agent_id: str, objective_bundle: dict, context: dict) -> Session:
        session = Session(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            status="pending",
            objective_bundle=objective_bundle,
            context=context,
        )
        self._sessions[session.id] = session
        asyncio.create_task(self._run(session))
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def cancel_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.status = "cancelled"
        return True

    async def _run(self, session: Session):
        session.status = "running"
        try:
            objectives = session.objective_bundle.get("objectives", [])
            startup_name = session.context.get("startup_name", "startup")

            if self._client:
                prompt = (
                    f"Eres un agente de venture studio. Ejecuta los siguientes objetivos "
                    f"para la startup '{startup_name}':\n{objectives}\n"
                    f"Contexto adicional: {session.context}\n"
                    "Responde con un plan de acción concreto y accionable."
                )
                message = await self._client.messages.create(
                    model=DEFAULT_MODEL,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                output = message.content[0].text
            else:
                output = f"[Demo] Sesión {session.id} completada para {startup_name}."

            session.result = {"output": output, "objectives_count": len(objectives)}
            session.status = "completed"

            # Sincronizar con Notion
            try:
                from app.services.notion_sync import record_session
                record_session(
                    session_id=session.id,
                    agent_id_notion=session.context.get("agent_notion_id"),
                    status="completed",
                    result_summary=output[:200],
                )
            except Exception:
                pass

        except Exception as exc:
            session.result = {"error": str(exc)}
            session.status = "failed"
            try:
                from app.services.notion_sync import record_session
                record_session(session.id, None, "failed")
            except Exception:
                pass


runtime_service = RuntimeService()
