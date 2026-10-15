from types import SimpleNamespace

import pytest
from mcp import types

from gateway import server
from gateway.upstreams import UpstreamTools

WRITE_TOOL = "woocommerce_create_product"


def make_ctx(role):
    user = {"id": 1, "name": "Tester", "email": "t@example.com", "role": role}
    return SimpleNamespace(request=SimpleNamespace(scope={"urumi_user": user}))


def fake_tool(name):
    return SimpleNamespace(
        name=name, description="a tool", input_schema={"type": "object"}, output_schema=None
    )


@pytest.fixture
def fake_upstreams(monkeypatch):
    """One fake WooCommerce server with a read tool and a write tool. Audit entries are collected."""

    async def fake_list_all_tools():
        tools = [fake_tool("list_orders"), fake_tool("create_product")]
        return [UpstreamTools(name="woocommerce", reachable=True, tools=tools, error=None)]

    calls = []
    audit = []

    async def fake_call_tool_on(full_name, arguments):
        calls.append(full_name)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="done")], is_error=False
        )

    async def fake_record(user, full_name, duration_ms, outcome):
        audit.append((full_name, outcome))

    monkeypatch.setattr(server, "list_all_tools", fake_list_all_tools)
    monkeypatch.setattr(server, "call_tool_on", fake_call_tool_on)
    monkeypatch.setattr(server, "record", fake_record)
    return SimpleNamespace(calls=calls, audit=audit)


@pytest.mark.asyncio
async def test_member_does_not_see_the_write_tool(fake_upstreams):
    result = await server.list_tools(make_ctx("member"), None)
    names = [tool.name for tool in result.tools]
    assert names == ["woocommerce_list_orders"]


@pytest.mark.asyncio
async def test_admin_sees_every_tool(fake_upstreams):
    result = await server.list_tools(make_ctx("admin"), None)
    names = [tool.name for tool in result.tools]
    assert names == ["woocommerce_list_orders", WRITE_TOOL]


@pytest.mark.asyncio
async def test_member_is_refused_when_calling_the_write_tool_anyway(fake_upstreams):
    params = SimpleNamespace(name=WRITE_TOOL, arguments={})
    result = await server.call_tool(make_ctx("member"), params)
    assert result.is_error
    assert "permission" in result.content[0].text
    assert fake_upstreams.calls == []  # the upstream server was never contacted
    assert fake_upstreams.audit == [(WRITE_TOOL, "denied")]


@pytest.mark.asyncio
async def test_admin_can_call_the_write_tool(fake_upstreams):
    params = SimpleNamespace(name=WRITE_TOOL, arguments={})
    result = await server.call_tool(make_ctx("admin"), params)
    assert not result.is_error
    assert fake_upstreams.calls == [WRITE_TOOL]
    assert fake_upstreams.audit == [(WRITE_TOOL, "success")]


@pytest.mark.asyncio
async def test_a_request_with_no_user_gets_nothing(fake_upstreams):
    ctx = SimpleNamespace(request=None)
    assert (await server.list_tools(ctx, None)).tools == []
    result = await server.call_tool(ctx, SimpleNamespace(name="woocommerce_list_orders", arguments={}))
    assert result.is_error
    assert fake_upstreams.calls == []