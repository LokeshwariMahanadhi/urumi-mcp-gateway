import pytest

from gateway import auth
from gateway.auth import AuthMiddleware

ADMIN = {"id": 1, "name": "Ann", "email": "ann@example.com", "role": "admin"}


async def send_request(monkeypatch, headers, database_down=False):
    """Run one request through AuthMiddleware. Returns (status, what the app behind it saw)."""

    def fake_find_user_by_key(key):
        if database_down:
            raise RuntimeError("database is down")
        return ADMIN if key == "good-key" else None

    monkeypatch.setattr(auth, "find_user_by_key", fake_find_user_by_key)

    seen = {}

    async def inner_app(scope, receive, send):
        seen["user"] = scope.get("urumi_user")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    sent = []

    async def send(message):
        sent.append(message)

    async def receive():
        return {"type": "http.request"}

    scope = {"type": "http", "headers": headers}
    await AuthMiddleware(inner_app)(scope, receive, send)
    return sent[0]["status"], seen


@pytest.mark.asyncio
async def test_no_key_is_refused_and_app_is_never_reached(monkeypatch):
    status, seen = await send_request(monkeypatch, headers=[])
    assert status == 401
    assert seen == {}


@pytest.mark.asyncio
async def test_wrong_key_is_refused(monkeypatch):
    status, seen = await send_request(monkeypatch, [(b"authorization", b"Bearer nope")])
    assert status == 401
    assert seen == {}


@pytest.mark.asyncio
async def test_good_key_gets_in_and_user_is_passed_on(monkeypatch):
    status, seen = await send_request(monkeypatch, [(b"authorization", b"Bearer good-key")])
    assert status == 200
    assert seen["user"] == ADMIN


@pytest.mark.asyncio
async def test_if_the_database_is_down_nobody_gets_in(monkeypatch):
    status, seen = await send_request(
        monkeypatch, [(b"authorization", b"Bearer good-key")], database_down=True
    )
    assert status == 503
    assert seen == {}