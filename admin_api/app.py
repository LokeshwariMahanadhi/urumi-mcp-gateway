"""The admin API: what the dashboard talks to."""
from typing import Literal

import psycopg
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from admin_api import catalog, chat, limits, queries, servers
from admin_api.sessions import make_token, read_token
from gateway.permissions import can_use_tool
from gateway.urlcheck import UrlRejected, check_upstream_url
from gateway.accounts import (
    create_key,
    create_user,
    find_user_by_key,
    get_user_by_id,
    revoke_key,
    revoke_own_key,
)

app = FastAPI(title="Urumi gateway admin API")
bearer = HTTPBearer(auto_error=False)

# The dashboard runs on its own address while we develop, so the browser needs permission to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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


class NewServer(BaseModel):
    # Lower case letters and digits only: the gateway builds tool names as servername_toolname.
    name: str = Field(pattern=r"^[a-z0-9]+$", max_length=40)
    url: str
    credential: str = ""


class ChatMessage(BaseModel):
    # Only these two roles are accepted, so the browser cannot slip in system or tool messages.
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class EditServer(BaseModel):
    url: str
    # None keeps the saved credential. An empty string removes it.
    credential: str | None = None


class EnabledFlag(BaseModel):
    enabled: bool


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


@app.get("/api/me/keys")
def my_keys(user=Depends(current_user)):
    """Every signed-in person can see their own keys, and nobody else's."""
    return queries.list_keys_of(user["id"])


@app.post("/api/me/keys", status_code=201)
def make_my_key(body: NewKey, user=Depends(current_user)):
    # The key is always made for the person who is signed in, never for someone else.
    return {"key": create_key(user["id"], body.label)}


@app.post("/api/me/keys/{key_id}/revoke")
def revoke_my_key(key_id: int, user=Depends(current_user)):
    if not revoke_own_key(key_id, user["id"]):
        raise HTTPException(status_code=404, detail="No such key.")
    return {"revoked": True}


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


@app.get("/api/servers/health")
async def servers_health(admin=Depends(admin_only)):
    return await catalog.server_health()


@app.get("/api/tools")
async def tools(user=Depends(current_user)):
    return await catalog.tool_catalog(user["role"])


@app.get("/api/servers")
def list_servers(admin=Depends(admin_only)):
    return servers.list_servers()


@app.post("/api/servers", status_code=201)
def add_server(body: NewServer, admin=Depends(admin_only)):
    try:
        check_upstream_url(body.url)
    except UrlRejected as problem:
        raise HTTPException(status_code=400, detail=str(problem))
    try:
        server_id = servers.add_server(body.name, body.url, body.credential)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="A server with that name already exists.")
    return {"id": server_id}


@app.put("/api/servers/{server_id}")
def edit_server(server_id: int, body: EditServer, admin=Depends(admin_only)):
    try:
        check_upstream_url(body.url)
    except UrlRejected as problem:
        raise HTTPException(status_code=400, detail=str(problem))
    if not servers.update_server(server_id, body.url, body.credential):
        raise HTTPException(status_code=404, detail="No such server.")
    return {"updated": True}


@app.post("/api/servers/{server_id}/enabled")
def switch_server(server_id: int, body: EnabledFlag, admin=Depends(admin_only)):
    if not servers.set_enabled(server_id, body.enabled):
        raise HTTPException(status_code=404, detail="No such server.")
    return {"enabled": body.enabled}


@app.delete("/api/servers/{server_id}")
def remove_server(server_id: int, admin=Depends(admin_only)):
    if not servers.delete_server(server_id):
        raise HTTPException(status_code=404, detail="No such server.")
    return {"deleted": True}


@app.post("/api/chat")
async def chat_with_agent(body: ChatRequest, user=Depends(current_user)):
    """Answer a question with the AI model. Its tool calls go through the gateway as the signed-in user."""
    if body.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message must be from you.")
    if not limits.allow(user["id"]):
        raise HTTPException(status_code=429, detail="You are sending messages too fast. Please wait a few minutes.")
    history = [{"role": message.role, "content": message.content} for message in body.messages]
    try:
        return await chat.run_chat(user, history)
    except chat.ChatError as problem:
        raise HTTPException(status_code=503, detail=str(problem))
    except Exception:
        raise HTTPException(status_code=502, detail="The chat could not reach the gateway. Is it running?")


@app.get("/api/audit")
def audit(limit: int = Query(100, ge=1, le=500), admin=Depends(admin_only)):
    return queries.list_audit(limit)


# Keep this at the very bottom: it starts the admin API.
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8300)