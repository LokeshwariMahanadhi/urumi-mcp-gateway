import time

import jwt
import pytest

from gateway import auth, delegation

ADMIN = {"id": 1, "name": "Ann", "email": "ann@example.com", "role": "admin"}


@pytest.fixture(autouse=True)
def secret(monkeypatch):
    monkeypatch.setenv("CHAT_GATEWAY_SECRET", "test-secret-that-is-long-enough-for-hs256")


def test_a_fresh_token_gives_back_the_user_number():
    token = delegation.make_delegation_token(7)
    assert delegation.read_delegation_token(token) == 7


def test_a_token_signed_with_another_secret_is_refused(monkeypatch):
    token = delegation.make_delegation_token(7)
    monkeypatch.setenv("CHAT_GATEWAY_SECRET", "a-different-secret-that-is-long-enough-for-hs256")
    assert delegation.read_delegation_token(token) is None


def test_an_expired_token_is_refused():
    old = int(time.time()) - 1000
    token = jwt.encode(
        {"sub": "7", "aud": delegation.AUDIENCE, "iat": old, "exp": old + 120},
        "test-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
    )
    assert delegation.read_delegation_token(token) is None


def test_a_token_meant_for_something_else_is_refused():
    now = int(time.time())
    token = jwt.encode(
        {"sub": "7", "aud": "somewhere-else", "iat": now, "exp": now + 120},
        "test-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
    )
    assert delegation.read_delegation_token(token) is None


def test_a_dashboard_session_token_does_not_work_at_the_gateway(monkeypatch):
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "test-secret-that-is-long-enough-for-hs256")
    from admin_api.sessions import make_token

    assert delegation.read_delegation_token(make_token(7)) is None


async def send_through_middleware(monkeypatch, key):
    monkeypatch.setattr(auth, "find_user_by_key", lambda value: None)
    monkeypatch.setattr(auth, "user_from_delegation_token", lambda value: ADMIN if value == "aaa.bbb.ccc" else None)
    seen = {}

    async def inner_app(scope, receive, send):
        seen["user"] = scope.get("urumi_user")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    sent = []

    async def send(message):
        sent.append(message)

    async def receive():
        return {"type": "http.request", "body": b""}

    scope = {"type": "http", "headers": [(b"authorization", f"Bearer {key}".encode())]}
    await auth.AuthMiddleware(inner_app)(scope, receive, send)
    return sent[0]["status"], seen.get("user")


@pytest.mark.asyncio
async def test_the_gateway_accepts_a_valid_delegation_token(monkeypatch):
    status, user = await send_through_middleware(monkeypatch, "aaa.bbb.ccc")
    assert status == 200
    assert user == ADMIN


@pytest.mark.asyncio
async def test_the_gateway_refuses_a_bad_delegation_token(monkeypatch):
    status, user = await send_through_middleware(monkeypatch, "xxx.yyy.zzz")
    assert status == 401
    assert user is None
