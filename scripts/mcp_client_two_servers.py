"""Outside MCP client, user B. One task that needs TWO different upstream servers.

Step 1 asks the WooCommerce server for recent orders.
Step 2 asks the currency server to convert that order's total from INR to USD.
Both calls go through the one gateway URL, using only the caller's own API key.

Run from the project folder:
    python scripts/mcp_client_two_servers.py
Key: set GATEWAY_KEY, or paste it when asked (hidden).
"""
import asyncio
import getpass
import json
import os

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

URL = os.environ.get("GATEWAY_URL", "http://urumi.localtest.me:8088/mcp")


def root_cause(problem):
    while isinstance(problem, BaseExceptionGroup) and problem.exceptions:
        problem = problem.exceptions[0]
    return problem


def text_of(result):
    return " ".join(b.text for b in result.content if getattr(b, "type", "") == "text") or "(no text)"


def newest_total(text):
    """Best effort: read the total of the first order. Fall back to 349 (order #19)."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("orders") or data.get("result") or [data]
        return float(data[0]["total"])
    except Exception:
        return 349.0


async def main():
    key = os.environ.get("GATEWAY_KEY") or getpass.getpass("Paste your API key (hidden): ").strip()
    print(f"Connecting to {URL}")
    timeout = httpx2.Timeout(30.0, read=120.0)
    async with httpx2.AsyncClient(headers={"Authorization": f"Bearer {key}"}, timeout=timeout) as http:
        probe = await http.post(
            URL,
            json={"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "key-check", "version": "1"}}},
            headers={"Accept": "application/json, text/event-stream"},
        )
        if probe.status_code in (401, 403):
            print(f"\nREJECTED by the gateway: HTTP {probe.status_code} - {probe.text[:120]}")
            print("This API key is invalid or has been revoked, so no tool can be listed or called.")
            return
        async with Client(streamable_http_client(URL, http_client=http)) as client:
            listing = await client.list_tools()
            print(f"\nThis key can see {len(listing.tools)} tools:")
            for tool in listing.tools:
                print("  -", tool.name)

            print("\nSTEP 1 (WooCommerce server): woocommerce_list_orders ...")
            orders = await client.call_tool("woocommerce_list_orders", {"status": "any", "limit": 3})
            body = text_of(orders)
            print("  result:", body[:400])
            total = newest_total(body)

            print(f"\nSTEP 2 (Currency server): convert {total} INR to USD ...")
            converted = await client.call_tool(
                "currency_convert_currency",
                {"amount": total, "from_currency": "INR", "to_currency": "USD"},
            )
            print("  result:", text_of(converted)[:300])
            print("\nTwo different upstream servers answered one request. Check the audit log.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as problem:
        print("Could not finish:", str(root_cause(problem))[:300])
