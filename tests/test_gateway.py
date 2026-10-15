"""Tests for the gateway routing. These need no running servers."""
import asyncio

import pytest

from gateway import upstreams
from gateway.upstreams import (
    GatewayError,
    call_tool_on,
    list_all_tools,
    prefixed_name,
    split_tool_name,
)

# Nothing listens on this port, so connecting to it fails straight away.
DEAD_URL = "http://127.0.0.1:9/mcp"


def test_prefixed_name_puts_the_server_first():
    assert prefixed_name("currency", "ping") == "currency_ping"


def test_two_servers_can_share_a_tool_name():
    assert prefixed_name("currency", "ping") != prefixed_name("utilities", "ping")


def test_split_tool_name():
    assert split_tool_name("currency_ping") == ("currency", "ping")


def test_split_keeps_underscores_in_the_tool_name():
    assert split_tool_name("woocommerce_list_orders") == ("woocommerce", "list_orders")


def test_split_rejects_a_name_without_a_server():
    with pytest.raises(GatewayError) as problem:
        split_tool_name("justaname")
    assert "server_tool" in str(problem.value)


@pytest.mark.asyncio
async def test_unknown_server_gives_a_clear_error():
    with pytest.raises(GatewayError) as problem:
        await call_tool_on("nothing_here", {})
    assert "no server called 'nothing'" in str(problem.value)


@pytest.mark.asyncio
async def test_dead_server_gives_a_clear_error(monkeypatch):
    monkeypatch.setattr(upstreams, "UPSTREAMS", {"ghost": DEAD_URL})
    with pytest.raises(GatewayError) as problem:
        await call_tool_on("ghost_ping", {})
    assert "'ghost' server is not reachable" in str(problem.value)


@pytest.mark.asyncio
async def test_slow_server_times_out(monkeypatch):
    class SlowClient:
        """A fake upstream that never answers in time."""

        def __init__(self, url):
            pass

        async def __aenter__(self):
            await asyncio.sleep(5)
            return self

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(upstreams, "UPSTREAMS", {"slow": "http://example.invalid/mcp"})
    monkeypatch.setattr(upstreams, "Client", SlowClient)
    monkeypatch.setattr(upstreams, "CALL_TIMEOUT_SECONDS", 1.0)

    with pytest.raises(GatewayError) as problem:
        await call_tool_on("slow_ping", {})
    assert "did not answer" in str(problem.value)


@pytest.mark.asyncio
async def test_listing_marks_a_dead_server_but_does_not_crash(monkeypatch):
    monkeypatch.setattr(upstreams, "UPSTREAMS", {"ghost": DEAD_URL})

    results = await list_all_tools()

    assert len(results) == 1
    assert results[0].name == "ghost"
    assert results[0].reachable is False
    assert results[0].tools == []