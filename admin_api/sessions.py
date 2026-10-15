"""Login session tokens for the dashboard."""
import os
import time

import jwt

SESSION_HOURS = 8


def _secret():
    secret = os.environ.get("ADMIN_SESSION_SECRET")
    if not secret:
        raise RuntimeError("Missing setting: ADMIN_SESSION_SECRET")
    return secret


def make_token(user_id):
    """A signed token that says 'this is user N' and stops working after 8 hours."""
    now = int(time.time())
    payload = {"sub": str(user_id), "iat": now, "exp": now + SESSION_HOURS * 3600}
    return jwt.encode(payload, _secret(), algorithm="HS256")


def read_token(token):
    """The user number inside a valid token, or None if it is fake or expired."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None