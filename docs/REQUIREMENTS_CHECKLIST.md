# Requirements Checklist

Status values: NOT STARTED, IN PROGRESS, DONE (with evidence), BLOCKED.
Only mark DONE when it has been tested and the evidence is recorded.

## Core components
| Requirement | Status | Evidence |
|---|---|---|
| Custom WooCommerce MCP server (5 tools) | NOT STARTED | |
| Gateway with one authenticated MCP endpoint (Streamable HTTP) | NOT STARTED | |
| At least 3 running upstream MCP servers | NOT STARTED | |
| Tool discovery, namespacing, routing, timeouts, failure isolation | NOT STARTED | |
| Admin and member roles, enforced on the server | NOT STARTED | |
| Hashed, revocable API keys | NOT STARTED | |
| Audit logs (user, upstream, tool, time, duration, outcome) | NOT STARTED | |
| React dashboard | NOT STARTED | |
| AI chat with real tool calling | NOT STARTED | |
| WordPress + WooCommerce with persistent data | NOT STARTED | |
| Docker, kind, Helm, k3s on a VPS | NOT STARTED | |

## Environment (Day 1)
| Item | Status | Evidence |
|---|---|---|
| Docker Desktop engine works | DONE | hello-world ran |
| kubectl, Helm, kind installed | DONE | version commands ran |
| Repo created and first push | DONE | commit 9ea7510 |
| MCP SDK 2.3.0 imports on Python 3.13.1 | DONE | import check passed |