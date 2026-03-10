"""BaseAgent - base class for all Venture Studio AI agents."""
import abc, logging, os, time
from typing import Any, Optional
import anthropic
from packages.agent_sdk.types import AgentContext, AgentResult, AgentStatus

class BaseAgent(abc.ABC):
    agent_id:     str = "base-agent"
    agent_name:   str = "Base Agent"
    model:        str = "claude-sonnet-4-6"
    max_tokens:   int = 2048
    system_prompt: str = "You are a specialized AI agent of the AI Venture Studio OS."

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        self.log = logging.getLogger(f"agent.{self.agent_id}")

    @abc.abstractmethod
    async def execute(self, ctx: AgentContext) -> AgentResult: ...

    async def run(self, ctx: AgentContext) -> AgentResult:
        start = time.perf_counter()
        self.log.info(f"[{ctx.task_id}] Starting")
        try:
            result = await self.execute(ctx)
            result.duration_ms = round((time.perf_counter() - start) * 1000)
            self.log.info(f"[{ctx.task_id}] Done in {result.duration_ms}ms")
            return result
        except Exception as e:
            ms = round((time.perf_counter() - start) * 1000)
            self.log.error(f"[{ctx.task_id}] Error: {e}")
            return AgentResult(task_id=ctx.task_id, agent_id=self.agent_id,
                               status=AgentStatus.ERROR, error=str(e), duration_ms=ms)

    def call_llm(self, prompt: str, system: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        r = self._client.messages.create(
            model=self.model, max_tokens=max_tokens or self.max_tokens,
            system=system or self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text
