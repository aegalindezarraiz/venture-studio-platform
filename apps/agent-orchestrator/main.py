"""Agent Orchestrator - coordinates agent execution. Port: 8001"""
import json, os, uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Agent Orchestrator - started")
    yield

app = FastAPI(title="Agent Orchestrator", version="1.0.0", lifespan=lifespan)

class TaskRequest(BaseModel):
    agent_id: str
    task_type: str
    payload: dict
    priority: int = 2
    callback_url: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-orchestrator"}

@app.post("/orchestrate/run")
async def run_task(req: TaskRequest):
    task_id = str(uuid.uuid4())
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        task = {"id": task_id, "status": "queued", "created_at": datetime.now(timezone.utc).isoformat(), **req.dict()}
        r.setex(f"task:{task_id}", 86400, json.dumps(task))
        r.lpush("task_queue", task_id)
        r.close()
    except Exception as e:
        pass
    return {"task_id": task_id, "status": "queued", "agent_id": req.agent_id}

@app.get("/orchestrate/tasks/{task_id}")
async def task_status(task_id: str):
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        data = r.get(f"task:{task_id}")
        r.close()
        if data:
            return json.loads(data)
    except Exception:
        pass
    return {"task_id": task_id, "status": "not_found"}

@app.get("/orchestrate/queue/stats")
async def queue_stats():
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        depth = r.llen("task_queue")
        r.close()
        return {"queued_tasks": depth}
    except Exception as e:
        return {"queued_tasks": 0, "error": str(e)}
