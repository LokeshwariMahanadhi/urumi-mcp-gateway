"""Checks the API key on every request before it reaches the MCP gateway."""
import asyncio
import json

from gateway.accounts import find_user_by_key


def _bearer_key(scope):
    """Pull the key out of the 'Authorization: Bearer <key>' header."""
    headers = dict(scope["headers"])
    value = headers.get(b"authorization", b"").decode()
    if value.startswith("Bearer "):
        return value[len("Bearer "):].strip()
    return None


async def _reject(send, status, message):
    body = json.dumps({"error": message}).encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})


class AuthMiddleware:
    """Wraps the gateway app. No valid key means the request stops here."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        key = _bearer_key(scope)
        if not key:
            await _reject(send, 401, "Missing API key.")
            return

        try:
            # The database library is not async, so run it in a worker thread.
            user = await asyncio.to_thread(find_user_by_key, key)
        except Exception:
            # If we cannot check the key, we let nobody in.
            await _reject(send, 503, "Cannot check API keys right now.")
            return

        if user is None:
            await _reject(send, 401, "Invalid or revoked API key.")
            return

        scope["urumi_user"] = user
        await self.app(scope, receive, send)