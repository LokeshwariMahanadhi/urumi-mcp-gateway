"""The admin API: what the dashboard talks to."""
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from admin_api.sessions import make_token, read_token
from gateway.accounts import find_user_by_key, get_user_by_id

app = FastAPI(title="Urumi gateway admin API")
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    api_key: str


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


# Keep this at the very bottom: it starts the admin API.
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8300)