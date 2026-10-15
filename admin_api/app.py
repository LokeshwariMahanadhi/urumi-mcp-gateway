"""The admin API: what the dashboard talks to."""
from typing import Literal

import psycopg
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from admin_api import queries
from admin_api.sessions import make_token, read_token
from gateway.accounts import (
    create_key,
    create_user,
    find_user_by_key,
    get_user_by_id,
    revoke_key,
)

app = FastAPI(title="Urumi gateway admin API")
bearer = HTTPBearer(auto_error=False)

# The dashboard runs on its own address while we develop, so the browser needs permission to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


class LoginRequest(BaseModel):
    api_key: str


class NewUser(BaseModel):
    email: str
    name: str
    role: Literal["admin", "member"]


class NewKey(BaseModel):
    label: str = ""


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """Who is calling? Read from the token, and look them up fresh every time,
    so a changed role or a deleted user takes effect at once."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Please log in.")
    user_id = read_token(credentials.credentials)
    user = get_user_by_id(user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Your session is not valid. Please log in again.")
    return user


def admin_only(user=Depends(current_user)):
    """For endpoints that only admins may use."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only.")
    return user


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/login")
def login(body: LoginRequest):
    user = find_user_by_key(body.api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key.")
    return {"token": make_token(user["id"]), "user": user}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


@app.get("/api/users")
def users(admin=Depends(admin_only)):
    return queries.list_users()


@app.post("/api/users", status_code=201)
def add_user(body: NewUser, admin=Depends(admin_only)):
    try:
        user_id = create_user(body.email, body.name, body.role)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="That email is already registered.")
    return {"id": user_id}


@app.get("/api/keys")
def keys(admin=Depends(admin_only)):
    return queries.list_keys()


@app.post("/api/users/{user_id}/keys", status_code=201)
def add_key(user_id: int, body: NewKey, admin=Depends(admin_only)):
    if get_user_by_id(user_id) is None:
        raise HTTPException(status_code=404, detail="No such user.")
    # The real key is in this answer once. After this it can never be read again.
    return {"key": create_key(user_id, body.label)}


@app.post("/api/keys/{key_id}/revoke")
def revoke(key_id: int, admin=Depends(admin_only)):
    revoke_key(key_id)
    return {"revoked": True}


@app.get("/api/audit")
def audit(limit: int = Query(100, ge=1, le=500), admin=Depends(admin_only)):
    return queries.list_audit(limit)


# Keep this at the very bottom: it starts the admin API.
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8300)