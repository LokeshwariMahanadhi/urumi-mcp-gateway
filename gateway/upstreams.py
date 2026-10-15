"""Talks to the upstream MCP servers: asks each one for its tools."""
import asyncio
from dataclasses import dataclass, field

from mcp import Client

# The upstream servers the gateway knows about.
# Later these will come from the database, added by an admin in the dashboard.
# Server names must NOT contain an underscore, because we use "_" to join
# the server name and the tool name (for example "currency_ping").
UPSTREAMS = {
    "woocommerce": "http://127.0.0.1:8101/mcp",
    "currency": "http://127.0.0.1:8102/mcp",
    "utilities": "http://127.0.0.1:8103/mcp",
}

# How long we wait for one upstream server before giving up.
TIMEOUT_SECONDS = 5.0


@dataclass
class UpstreamTools:
    """The result of asking one upstream server for its tools."""

    name: str
    reachable: bool
    tools: list = field(default_factory=list)
    error: str = ""


def prefixed_name(upstream, tool_name):
    """Give a tool its server name in front, so two servers can share a tool name."""
    return f"{upstream}_{tool_name}"


async def list_tools_of(name, url):
    """Ask one upstream server for its tools. Never raises: a dead server is reported."""
    try:
        async with asyncio.timeout(TIMEOUT_SECONDS):
            async with Client(url) as client:
                listing = await client.list_tools()
        return UpstreamTools(name=name, reachable=True, tools=listing.tools)
    except TimeoutError:
        return UpstreamTools(
            name=name,
            reachable=False,
            error=f"No answer within {TIMEOUT_SECONDS:.0f} seconds.",
        )
    except Exception as error:
        return UpstreamTools(
            name=name,
            reachable=False,
            error=f"Could not connect ({type(error).__name__}).",
        )


async def list_all_tools():
    """Ask every upstream server at the same time, and collect the answers."""
    jobs = [list_tools_of(name, url) for name, url in UPSTREAMS.items()]
    return await asyncio.gather(*jobs)