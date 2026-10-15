from types import SimpleNamespace

import pytest
from mcp import types

from gateway import server

USER = {"id": 1, "name": "Tester", "email": "t@example.com", "role": "admin"}
CTX = SimpleNamespace(request=SimpleNamespace(scope={"urumi_user": USER}))


@pytest.mark.asyncio
async def test_a_call_refreshes_the_server_list_before_running(monkeypatch):
    steps = []

    async def fake_refresh():
        steps.append("refresh")

    async def fake_call_tool_on(full_name, arguments):
        steps.append("call")
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="ok")], is_error=False
        )

    async def fake_record(user, full_name, duration_ms, outcome):
        pass

    monkeypatch.setattr(server, "refresh_upstreams", fake_refresh)
    monkeypatch.setattr(server, "call_tool_on", fake_call_tool_on)
    monkeypatch.setattr(server, "record", fake_record)

    await server.call_tool(CTX, SimpleNamespace(name="currency_ping", arguments={}))
    assert steps == ["refresh", "call"]


@pytest.mark.asyncio
async def test_listing_tools_refreshes_the_server_list(monkeypatch):
    steps = []

    async def fake_refresh():
        steps.append("refresh")

    async def fake_list_all_tools():
        steps.append("list")
        return []

    monkeypatch.setattr(server, "refresh_upstreams", fake_refresh)
    monkeypatch.setattr(server, "list_all_tools", fake_list_all_tools)

    await server.list_tools(CTX, None)
    assert steps == ["refresh", "list"]