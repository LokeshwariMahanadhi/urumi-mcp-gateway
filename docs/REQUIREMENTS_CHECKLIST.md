# Requirements checklist

Honest status of every requirement. "DONE" always has evidence. Updated 15 Oct 2026 (Day 4).

## Core requirements

| Requirement | Status | Evidence |
|---|---|---|
| Custom WooCommerce MCP server (5 tools) | DONE | Port 8101; tested in MCP Inspector; commit 5b8c19c |
| WordPress + WooCommerce, data kept across restarts | IN PROGRESS | Docker Compose with named volumes (local). Kubernetes version not done yet |
| At least 3 upstream MCP servers | DONE | woocommerce, currency (2eb5e77), utilities (a8d420b) |
| One gateway endpoint (Streamable HTTP) | DONE | `http://127.0.0.1:8200/mcp` (22dd08f) |
| Tool discovery and namespacing | DONE | Tools appear as `servername_toolname`, for example `currency_ping` |
| Routing to the right upstream | DONE | `gateway/upstreams.py`, tested |
| Timeouts | DONE | 5 s for listing, 15 s for calls |
| Failure isolation | DONE | A stopped upstream is marked unreachable; the others keep working and it recovers without a restart |
| Admin and member roles, enforced on the server | DONE | Member sees 8 tools, is refused the write tool (0a89702, 5 role tests) |
| API keys: hashed and revocable | DONE | Only a SHA-256 hash is stored; shown once; revoke proven (be5d502) |
| Key required on the gateway | DONE | 401 with no key or a wrong key; 503 if the database is down (tests) |
| Audit log | DONE | One row per call, including refused calls and failures (a13da56) |
| Automated tests | DONE | 35 passing |
| Credentials never in logs | DONE | Signed-URL log leak found and fixed (5b8c19c) |
| Admin API for the dashboard | NOT STARTED | |
| React dashboard (login, servers, keys, audit log) | NOT STARTED | |
| Chat agent with real tool calling | NOT STARTED | |
| Dockerfiles for each service | NOT STARTED | |
| Helm charts (local and production values) | NOT STARTED | |
| Running on kind | NOT STARTED | |
| k3s on a VPS with TLS | NOT STARTED | |
| WooCommerce MCP server reachable only inside the cluster | NOT STARTED | |
| Place a test order on the storefront (cash on delivery) | NOT STARTED | |
| Connect an external MCP client (documented) | IN PROGRESS | Works locally with MCP Inspector; the README section is not written yet |

## Documents

| Item | Status | Evidence |
|---|---|---|
| README: local setup | IN PROGRESS | Written up to the WooCommerce server; gateway and security parts being added |
| README: VPS setup | NOT STARTED | |
| System design and tradeoffs note | NOT STARTED | |
| Threat model note | IN PROGRESS | `docs/SECURITY.md` covers keys, roles and audit log |
| List of bonus items | NOT STARTED | |
| Demo video | NOT STARTED | |
| Repository open to reviewers (it is private today) | NOT STARTED | |

## Environment (Day 1)

| Item | Status | Evidence |
|---|---|---|
| Docker Desktop engine works | DONE | hello-world ran |
| kubectl, Helm, kind installed | DONE | version commands ran |
| Repo created, first push | DONE | commit 9ea7510 |
| MCP SDK 2.3.0 imports on Python 3.13.1 | DONE | import check passed |
| PostgreSQL 16 in Docker | DONE | `db/docker-compose.yml` (007de21) |