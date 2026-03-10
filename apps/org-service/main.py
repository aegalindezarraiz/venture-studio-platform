"""Org Service - organizations, teams, and permissions. Port: 8011"""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Org Service - started")
    yield

app = FastAPI(title="Org Service", version="1.0.0", lifespan=lifespan)

class OrgCreate(BaseModel):
    name: str
    slug: str
    plan: str = "starter"

class MemberInvite(BaseModel):
    email: str
    role: str = "member"

@app.get("/health")
async def health():
    return {"status": "ok", "service": "org-service"}

@app.post("/organizations")
async def create_org(org: OrgCreate):
    return {"status": "created", "id": f"org_{org.slug}", **org.dict()}

@app.get("/organizations/{org_id}")
async def get_org(org_id: str):
    return {"id": org_id, "name": "Demo Org", "plan": "growth", "members": 5}

@app.post("/organizations/{org_id}/members")
async def invite_member(org_id: str, invite: MemberInvite):
    return {"status": "invited", **invite.dict(), "org_id": org_id}

@app.get("/organizations/{org_id}/members")
async def list_members(org_id: str):
    return {"org_id": org_id, "members": []}
