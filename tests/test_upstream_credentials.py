import pytest

from gateway import upstreams


def test_a_plain_credential_is_sent_as_a_bearer_token():
    assert upstreams.auth_headers("abc123") == {"Authorization": "Bearer abc123"}


def test_a_header_style_credential_is_sent_as_that_header():
    assert upstreams.auth_headers("X-Api-Key: abc123") == {"X-Api-Key": "abc123"}


def test_no_credential_means_no_headers():
    assert upstreams.auth_headers(None) == {}
    assert upstreams.auth_headers("") == {}


class FakeClient:
    """Stands in for the MCP client and remembers what it was given."""

    opened_with = None

    def __init__(self, target):
        FakeClient.opened_with = target

    async def __aenter__(self):
        return self

    async def __aexit__(self, *problem):
        return False


@pytest.mark.asyncio
async def test_without_a_credential_the_client_gets_just_the_address(monkeypatch):
    monkeypatch.setattr(upstreams, "Client", FakeClient)
    async with upstreams.connect_to("http://x/mcp"):
        pass
    assert FakeClient.opened_with == "http://x/mcp"


@pytest.mark.asyncio
async def test_with_a_credential_the_request_carries_the_header(monkeypatch):
    seen = {}

    def fake_transport(url, http_client):
        seen["url"] = url
        seen["headers"] = dict(http_client.headers)
        return "transport"

    monkeypatch.setattr(upstreams, "Client", FakeClient)
    monkeypatch.setattr(upstreams, "streamable_http_client", fake_transport)
    async with upstreams.connect_to("http://x/mcp", "secret-token"):
        pass
    assert seen["url"] == "http://x/mcp"
    assert seen["headers"]["authorization"] == "Bearer secret-token"
    assert FakeClient.opened_with == "transport"


@pytest.mark.asyncio
async def test_refresh_also_loads_the_credentials(monkeypatch):
    monkeypatch.setattr(upstreams, "UPSTREAMS", {})
    monkeypatch.setattr(upstreams, "CREDENTIALS", {})
    monkeypatch.setattr(upstreams, "load_upstreams_from_database", lambda: {"shop": "http://shop/mcp"})
    monkeypatch.setattr(upstreams, "load_credentials_from_database", lambda: {"shop": "token"})
    await upstreams.refresh_upstreams()
    assert upstreams.CREDENTIALS == {"shop": "token"}
