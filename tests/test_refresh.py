import pytest

from gateway import upstreams


@pytest.mark.asyncio
async def test_refresh_replaces_the_list_from_the_database(monkeypatch):
    monkeypatch.setattr(upstreams, "UPSTREAMS", {"old": "http://old/mcp"})
    monkeypatch.setattr(upstreams, "load_upstreams_from_database", lambda: {"new": "http://new/mcp"})
    await upstreams.refresh_upstreams()
    assert upstreams.UPSTREAMS == {"new": "http://new/mcp"}


@pytest.mark.asyncio
async def test_refresh_keeps_the_old_list_if_the_database_is_down(monkeypatch):
    def broken():
        raise RuntimeError("database is down")

    monkeypatch.setattr(upstreams, "UPSTREAMS", {"old": "http://old/mcp"})
    monkeypatch.setattr(upstreams, "load_upstreams_from_database", broken)
    await upstreams.refresh_upstreams()
    assert upstreams.UPSTREAMS == {"old": "http://old/mcp"}