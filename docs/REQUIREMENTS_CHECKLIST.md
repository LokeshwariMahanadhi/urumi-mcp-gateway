# Requirements checklist

Honest status of every requirement. "DONE" always has evidence. Evidence from the Kubernetes run was seen on a real kind cluster.

## Core requirements

| Requirement | Status | Evidence |
|---|---|---|
| Custom WooCommerce MCP server (5 tools) | DONE | `servers/woocommerce/`; tools called through the gateway and in the dashboard chat (list products, list orders, get order, update order status) |
| WordPress + WooCommerce, data kept across restarts | DONE | StatefulSet/Deployment with three bound persistent volumes; the whole cluster was shut down overnight and came back with the same pods and data |
| At least 3 upstream MCP servers | DONE | woocommerce, currency, utilities, shown "3 of 3 connected" in the dashboard |
| One gateway endpoint (Streamable HTTP) | DONE | `http://urumi.localtest.me:8088/mcp` through the Ingress; an outside client connected with only the URL and a key |
| Tool discovery and namespacing | DONE | Tools appear as `servername_toolname` (10 tools for an admin) |
| Routing to the right upstream | DONE | `gateway/upstreams.py`, tests, and live calls to all three servers |
| Timeouts | DONE | 5 s for listing, 15 s for calls; the dashboard showed "No answer within 5 seconds." for a stopped server |
| Failure isolation | DONE | Stopped the currency server on the cluster: "2 of 3 connected", the chat still listed products; it recovered with no gateway restart |
| Admin and member roles, enforced on the server | DONE | Member sees 8 tools, is refused `woocommerce_update_order_status` by the gateway and the chat; the admin's chat completed order 14 |
| API keys: hashed and revocable | DONE | Only a SHA-256 hash is stored; shown once; a revoked key was refused at sign-in on the cluster |
| Key required on the gateway | DONE | 401 for a wrong key (seen in the gateway log), 503 if the database is down (tests) |
| Audit log | DONE | One row per call, including `denied` (member, 0 ms) |
| Admin API and React dashboard (login, servers, tools, keys, audit) | DONE | Running on the cluster; roles change what each person sees |
| Chat agent with real tool calling, acting as the signed-in user | DONE | Tool trace shown under each answer; member and admin got different results |
| Automated tests | DONE | 97 passing; GitHub Actions runs them on every push |
| Credentials never in logs | DONE | Signed-URL log leak found and fixed |
| Dockerfiles for each service | DONE | `Dockerfile` (backend and MCP servers) and `frontend/Dockerfile`; built and loaded into kind |
| Helm chart, local and production values | DONE (production values not yet deployed) | `deploy/helm/urumi/`; installed and upgraded six revisions on kind |
| Running on kind | DONE | `kubectl get pods -n urumi` all `Running`; Ingress at `*.localtest.me:8088` |
| Ingress, PVCs, probes, requests and limits, Secrets | DONE | `kubectl get svc,ingress,pvc,secret -n urumi`; probes and resources in the chart |
| WooCommerce MCP server reachable only inside the cluster | DONE | `ClusterIP` only, not in the Ingress; a stranger pod timed out (curl exit 28) from the NetworkPolicy |
| Place a test order on the storefront (cash on delivery) | DONE | Order #14 placed at the storefront; the chat then listed and completed it |
| Connect an external MCP client (documented) | DONE | `scripts/mcp_client_demo.py`; README section |
| k3s on a VPS with TLS | NOT STARTED | Written in the README, not run yet |

## Definition-of-done flow (two users)

| Step | Status | Evidence |
|---|---|---|
| Member signs in, sees only read tools, cannot change an order | DONE | Member chat: no update tool; audit shows `denied` for a direct call |
| Admin signs in and changes the order | DONE | Order 14 completed through the chat |
| Audit log shows who did what | DONE | Rows for Admin and Member with outcome and duration |
| Revoke a key | DONE | The revoked key was refused |
| Disable a server | DONE | Currency off: 7 tools; on: 10 tools |
| Kill a pod | DONE | Deleted the WooCommerce MCP pod; a new one was Running in under 30 seconds |

## Documents

| Item | Status | Where |
|---|---|---|
| README: local setup, place an order, external client, chat | DONE | `README.md` |
| README: VPS setup | DONE (not yet run on a VPS) | `README.md` |
| System design and tradeoffs note | DONE | `docs/DESIGN.md` |
| Threat model note (four required points) | DONE | `docs/THREAT_MODEL.md` |
| List of bonus items | DONE | `README.md`, "Bonus and stand-out items" |
| Demo video | NOT STARTED | |
| Repository open to reviewers | NOT STARTED | Private until submission |

## Bonus and stand-out

| Item | Status |
|---|---|
| Per-tool permissions | DONE |
| SSRF check on server addresses | DONE |
| NetworkPolicies, non-root containers, read-only filesystem | DONE |
| Helm upgrade and rollback documented | DONE (rollback not demonstrated live) |
| Per-person chat rate limit | DONE (in memory) |
| Continuous integration | DONE |
| Observability: server health and audit log | PARTIAL (no Prometheus metrics) |
| More than one gateway replica | NOT STARTED |
| Per-key rate limit on `/mcp` | NOT STARTED |
| Encrypted upstream credentials | NOT STARTED |
