"""Short-lived tokens that let the chat agent call the gateway on behalf of a signed-in person.

The chat agent never sees anyone's API key (keys are stored hashed). Instead, the admin API
signs a token that says "this is user N" and stops working after two minutes. The gateway
checks the signature, looks the user up fresh, and then applies that user's role and audit log.
"""
import os
import time

import jwt

from gateway.accounts import get_user_by_id

AUDIENCE = "urumi-gateway"
LIFETIME_SECONDS = 120


def _secret():
    secret = os.environ.get("CHAT_GATEWAY_SECRET")
    if not secret:
        raise RuntimeError("Missing setting: CHAT_GATEWAY_SECRET")
    return secret


def make_delegation_token(user_id):
    now = int(time.time())
    payload = {"sub": str(user_id), "aud": AUDIENCE, "iat": now, "exp": now + LIFETIME_SECONDS}
    return jwt.encode(payload, _secret(), algorithm="HS256")


def read_delegation_token(token):
    """The user number inside a valid token, or None if it is fake, expired or meant for something else."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"], audience=AUDIENCE)
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def user_from_delegation_token(token):
    """The current user record for a valid token. Looked up fresh, so a deleted user stops working at once."""
    user_id = read_delegation_token(token)
    return get_user_by_id(user_id) if user_id else None
