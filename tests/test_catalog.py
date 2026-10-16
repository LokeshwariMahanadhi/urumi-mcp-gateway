from types import SimpleNamespace

import pytest

from admin_api import catalog

ROWS = [
    {"id": 1, "name": "woocommerce", "url": "http://x/1", "enabled": True, "has_credential": False},
    {"id": 2, "name": "currency", "url": "http://x/2", "enabled": True, "has_credential": False},
    {"id": 3, "name": "utilities", "url": "http://x/3", "enabled": False, "has_credential": False},
]


def tool(name, description="A tool.", read_only=None):
    annotations = None if read_only is None else SimpleNamespace(readOnlyHint=read_only)
    return SimpleNamespace(name=name, description=description, annotations=annotations)


@pytest.fixture
def fake_upstreams(monkeypatch):
    monkeypatch.setattr(catalog.servers, "list_servers", lambda: ROWS)

    async def fake_list_tools_of(name, url):
        if name == "currency":
            return SimpleNamespace(name=name, reachable=False, tools=[], error="Could not connect (OSError).")
        return SimpleNamespace(
            name=name,
            reachable=True,
            tools=[tool("list_orders"), tool("create_product"), tool("lookup", read_only=False)],
            error="",
        )

    monkeypatch.setattr(catalog, "list_tools_of", fake_list_tools_of)


@pytest.mark.asyncio
async def test_health_marks_up_down_and_disabled_servers(fake_upstreams):
    health = {entry["name"]: entry for entry in await catalog.server_health()}
    assert health["woocommerce"]["status"] == "up"
    assert health["woocommerce"]["tool_count"] == 3
    assert health["currency"]["status"] == "down"
    assert health["currency"]["error"]
    assert health["utilities"]["status"] == "disabled"
    assert health["utilities"]["latency_ms"] is None


@pytest.mark.asyncio
async def test_health_never_contains_the_raw_tool_objects(fake_upstreams):
    for entry in await catalog.server_health():
        assert "tools" not in entry


@pytest.mark.asyncio
async def test_catalog_only_lists_tools_of_working_servers(fake_upstreams):
    names = {entry["full_name"] for entry in await catalog.tool_catalog("admin")}
    assert "woocommerce_list_orders" in names
    assert not any(name.startswith("currency_") for name in names)


@pytest.mark.asyncio
async def test_a_member_sees_write_tools_locked(fake_upstreams):
    entries = {entry["full_name"]: entry for entry in await catalog.tool_catalog("member")}
    assert entries["woocommerce_create_product"]["locked"] is True
    assert entries["woocommerce_create_product"]["kind"] == "write"
    assert entries["woocommerce_list_orders"]["locked"] is False


@pytest.mark.asyncio
async def test_an_admin_has_nothing_locked(fake_upstreams):
    assert not any(entry["locked"] for entry in await catalog.tool_catalog("admin"))


@pytest.mark.asyncio
async def test_a_tool_with_a_not_read_only_hint_counts_as_write(fake_upstreams):
    entries = {entry["full_name"]: entry for entry in await catalog.tool_catalog("admin")}
    assert entries["woocommerce_lookup"]["kind"] == "write"
