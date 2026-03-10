"""Auth Service - JWT authentication and authorization. Port: 8010"""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-use-32-char-min")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Auth Service - started")
    yield

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    org_id: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service"}

@app.post("/auth/token", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    from jose import jwt
    payload = {
        "sub": form.username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
        "roles": ["founder"],
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "expires_in": EXPIRE_MINUTES * 60}

@app.post("/auth/register")
async def register(user: UserCreate):
    return {"status": "created", "email": user.email, "message": "Check your email for verification."}

@app.post("/auth/verify")
async def verify(token: str = Depends(oauth2)):
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "sub": payload.get("sub"), "roles": payload.get("roles", [])}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.post("/auth/refresh")
async def refresh(token: str = Depends(oauth2)):
    from jose import jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
        return {"access_token": jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
