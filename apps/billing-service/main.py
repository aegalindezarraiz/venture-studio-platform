"""Billing Service - subscriptions and payments. Port: 8012"""
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

PLANS = {
    "starter":    {"price_usd": 299,  "agents": 50,  "startups": 3},
    "growth":     {"price_usd": 799,  "agents": 200, "startups": 10},
    "enterprise": {"price_usd": 2499, "agents": 500, "startups": -1},
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Billing Service - started")
    yield

app = FastAPI(title="Billing Service", version="1.0.0", lifespan=lifespan)

class SubscriptionCreate(BaseModel):
    org_id: str
    plan: str
    payment_method_id: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "billing-service"}

@app.get("/billing/plans")
async def list_plans():
    return {"plans": PLANS}

@app.post("/billing/subscriptions")
async def create_subscription(req: SubscriptionCreate):
    if req.plan not in PLANS:
        raise HTTPException(400, f"Invalid plan. Options: {list(PLANS.keys())}")
    return {"status": "created", "org_id": req.org_id, "plan": req.plan, **PLANS[req.plan]}

@app.get("/billing/subscriptions/{org_id}")
async def get_subscription(org_id: str):
    return {"org_id": org_id, "plan": "growth", "status": "active", "next_billing": "2026-04-10"}

@app.delete("/billing/subscriptions/{org_id}")
async def cancel(org_id: str):
    return {"status": "cancelled", "org_id": org_id, "effective_date": "end_of_period"}
