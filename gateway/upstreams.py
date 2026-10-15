"""Talks to the upstream MCP servers: asks each one for its tools."""
import asyncio
from dataclasses import dataclass, field

from mcp import Client
from gateway.db import connect
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


# A call can take longer than a tool listing. This is longer than the 10 seconds
# the WooCommerce client waits for the store, so the store's own message arrives first.
CALL_TIMEOUT_SECONDS = 15.0


class GatewayError(Exception):
    """An error whose message is safe to show to the user or to the AI."""


def split_tool_name(full_name):
    """Split 'currency_convert_currency' into ('currency', 'convert_currency')."""
    upstream, separator, tool_name = full_name.partition("_")
    if not separator or not tool_name:
        raise GatewayError(f"'{full_name}' is not a valid tool name. Use server_tool.")
    return upstream, tool_name


async def call_tool_on(full_name, arguments):
    """Send a tool call to the right upstream server, with a time limit."""
    upstream, tool_name = split_tool_name(full_name)
    url = UPSTREAMS.get(upstream)
    if url is None:
        raise GatewayError(f"There is no server called '{upstream}'.")

    try:
        async with asyncio.timeout(CALL_TIMEOUT_SECONDS):
            async with Client(url) as client:
                return await client.call_tool(tool_name, arguments)
    except TimeoutError:
        raise GatewayError(
            f"The '{upstream}' server did not answer within {CALL_TIMEOUT_SECONDS:.0f} seconds."
        ) from None
    except Exception as error:
        raise GatewayError(f"The '{upstream}' server is not reachable.") from error

def load_upstreams_from_database():
    """Every enabled server in the database, as {name: url}."""
    with connect() as connection:
        rows = connection.execute(
            "SELECT name, url FROM upstream_servers WHERE enabled ORDER BY name"
        ).fetchall()
    return {name: url for name, url in rows}


async def refresh_upstreams():
    """Update the server list from the database.
    If the database cannot be reached, keep the list we already have."""
    try:
        found = await asyncio.to_thread(load_upstreams_from_database)
    except Exception:
        return
    UPSTREAMS.clear()
    UPSTREAMS.update(found)
