"""What the dashboard shows about the upstream servers: are they up, and which tools do they offer."""
import asyncio
import time

from admin_api import servers
from gateway.permissions import ADMIN_ONLY_TOOLS, can_use_tool
from gateway.upstreams import list_tools_of


def tool_kind(full_name, tool):
    """'write' if the tool changes the store, otherwise 'read'."""
    if full_name in ADMIN_ONLY_TOOLS:
        return "write"
    hint = getattr(getattr(tool, "annotations", None), "readOnlyHint", None)
    return "write" if hint is False else "read"


async def _probe(row):
    """Ask one server for its tools and time the answer. Never raises."""
    base = {
        "id": row["id"],
        "name": row["name"],
        "url": row["url"],
        "enabled": row["enabled"],
        "has_credential": row["has_credential"],
        "latency_ms": None,
        "tool_count": None,
        "error": "",
        "tools": [],
    }
    if not row["enabled"]:
        return {**base, "status": "disabled"}
    started = time.perf_counter()
    answer = await list_tools_of(row["name"], row["url"])
    latency = round((time.perf_counter() - started) * 1000)
    if not answer.reachable:
        return {**base, "status": "down", "latency_ms": latency, "error": answer.error}
    return {
        **base,
        "status": "up",
        "latency_ms": latency,
        "tool_count": len(answer.tools),
        "tools": answer.tools,
    }


async def _probe_all():
    rows = await asyncio.to_thread(servers.list_servers)
    return await asyncio.gather(*[_probe(row) for row in rows])


async def server_health():
    """One entry per server (disabled ones are listed but not contacted)."""
    results = await _probe_all()
    return [{key: value for key, value in result.items() if key != "tools"} for result in results]


async def tool_catalog(role):
    """Every tool of every reachable server. 'locked' marks tools this role may not use."""
    catalog = []
    for result in await _probe_all():
        for tool in result["tools"]:
            full_name = f"{result['name']}_{tool.name}"
            catalog.append(
                {
                    "server": result["name"],
                    "name": tool.name,
                    "full_name": full_name,
                    "description": (tool.description or "").strip(),
                    "kind": tool_kind(full_name, tool),
                    "locked": not can_use_tool(role, full_name),
                }
            )
    return catalog
