# Urumi MCP Gateway

A team MCP Gateway with a custom WooCommerce MCP server, built for the Urumi AI FDE internship assignment.

**Status:** work in progress (Days 2 to 4 done: WooCommerce MCP server, three upstream servers, the gateway, API keys, roles and audit log).

## What exists so far

- A WordPress + WooCommerce store in Docker, with data kept in named volumes.
- A custom WooCommerce MCP server with five tools:
  `list_products`, `create_product`, `list_orders`, `get_order`, `update_order_status`.
- Automated tests (pytest) for the WooCommerce client: settings, request signing, timeouts and error messages.

- Two more upstream servers (`currency`, `utilities`) and a gateway that gives one endpoint with namespaced tools, routing, timeouts and failure isolation.
- Hashed, revocable API keys, admin and member roles enforced on the server, and an audit log (see `docs/SECURITY.md`).
- 35 automated tests.

Still to come: the dashboard with AI chat, Docker images, Helm, kind and k3s.
See `docs/REQUIREMENTS_CHECKLIST.md` for the honest status of every requirement.

## How to run it (Windows, PowerShell)

1. Start the store:
```
   cd store
   docker compose up -d
```
   The store opens at http://127.0.0.1:8081 (port 8080 was already used on my machine).
2. Copy `.env.example` to `.env` and fill in the WooCommerce REST API key and secret
   (WooCommerce > Settings > Advanced > REST API). Never commit `.env`.
3. Create and activate a virtual environment, then install the packages:
   the official MCP Python SDK (2.3.0), `httpx2`, `pytest` and `pytest-asyncio`.
4. Start the WooCommerce MCP server from the project root:
```
   python -m servers.woocommerce.server
```
   It listens on http://127.0.0.1:8101/mcp (Streamable HTTP).
5. Try it with MCP Inspector: `npx @modelcontextprotocol/inspector`.

## Run the tests

```
pytest -v
```

The tests use fake store replies, so they do not need Docker or the real store.

## Design decisions

- **OAuth 1.0a for the store over plain HTTP.** WooCommerce refuses Basic auth over HTTP, so the client signs each request. On HTTPS (the k3s deployment) Basic auth can be used.
- **Clear errors for the AI.** Tools raise `ToolError` with a short readable message; other exceptions would be hidden by the SDK.
- **Privacy by design.** Order tools return the customer name only, never emails or addresses.
- **Input validation on the server.** Bad prices, stock values and order statuses are rejected before reaching the store.
- **No credentials in logs.** The HTTP library's request log printed signed URLs, so that logger is silenced.
- **Separation of concerns.** The store client and the MCP tools live in separate files.


## How this was built

I built this project with Claude (Anthropic) as an AI coding assistant, and I'm open about that. I decided what to build and worked through it step by step: I set up Docker and the WooCommerce store, created the products, the test order and the API keys (kept private, never committed), ran and tested every tool in MCP Inspector, diagnosed problems as they appeared (for example, port 8080 was already taken by another program, so I moved the store to 8081), ran the test suite, and committed and pushed each step. Claude helped write and explain the code along the way. I'm responsible for the project and can walk through how each part works. The commit history shows the AI help with `Co-Authored-By: Claude` lines.
