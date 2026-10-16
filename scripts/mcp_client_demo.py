"""A tiny outside MCP client. It connects to the gateway the way Claude Desktop or Cursor would.

Run it from the project folder:
    python scripts/mcp_client_demo.py

It asks for an API key (typed hidden), lists the tools that key may use, calls a safe tool,
then tries an admin-only tool so you can see what a member gets back.
Set GATEWAY_URL to point somewhere else (default: the local kind cluster).
"""
import asyncio
import getpass
import os

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

URL = os.environ.get("GATEWAY_URL", "http://urumi.localtest.me:8088/mcp")


def root_cause(problem):
    """The MCP client wraps errors in groups. Dig out the real one."""
    while isinstance(problem, BaseExceptionGroup) and problem.exceptions:
        problem = problem.exceptions[0]
    return problem


def text_of(result):
    return " ".join(block.text for block in result.content if getattr(block, "type", "") == "text") or "(no text)"


async def main():
    key = os.environ.get("GATEWAY_KEY") or getpass.getpass("Paste your API key (hidden): ").strip()
    print(f"Connecting to {URL}")
    timeout = httpx2.Timeout(30.0, read=120.0)
    async with httpx2.AsyncClient(headers={"Authorization": f"Bearer {key}"}, timeout=timeout) as http:
        async with Client(streamable_http_client(URL, http_client=http)) as client:
            listing = await client.list_tools()
            print(f"\nThis key can see {len(listing.tools)} tools:")
            for tool in listing.tools:
                print("  -", tool.name)

            print("\nCalling utilities_get_time ...")
            result = await client.call_tool("utilities_get_time", {})
            print("  result:", text_of(result)[:200])

            print("\nTrying the admin-only tool woocommerce_update_order_status ...")
            try:
                result = await client.call_tool("woocommerce_update_order_status", {"order_id": 14, "status": "completed"})
                answer = text_of(result)[:300]
                print("  ERROR RETURNED:" if result.is_error else "  ALLOWED, result:", answer)
            except Exception as problem:  # the gateway may refuse with a protocol error
                print("  REFUSED:", str(root_cause(problem))[:300])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as problem:
        print("Could not finish:", str(root_cause(problem))[:300])
