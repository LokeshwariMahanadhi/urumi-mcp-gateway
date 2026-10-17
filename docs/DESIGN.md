# System design and tradeoffs

## Architecture choices

- **Separate processes, one job each.** The gateway speaks MCP and enforces access. The admin API speaks HTTP/JSON to the dashboard.
  Each MCP server only knows its own tools. A bug or crash in one does not take down the others, and each has its own Deployment, limits and probes.
- **Streamable HTTP everywhere.** Clients, the gateway and the upstream servers all use the same MCP transport, so the gateway is just an
  MCP client on one side and an MCP server on the other.
- **Postgres for the control data.** Users, API keys (hashes only), the list of upstream servers and the audit log live in one small database.
  Server lists are in the database, not in a config file, so an admin can add, edit, disable or remove a server without a restart.
- **WordPress and WooCommerce run in the cluster** with MariaDB on a persistent volume. A Helm hook job sets up the store the first time.
- **Everything is a Helm chart** with a values file per environment. Names are fixed (for example `gateway`, `woocommerce-mcp`) so the
  services find each other without templated host names.

## How a tool call travels

1. A client sends `POST /mcp` with `Authorization: Bearer urumi_...` through the Ingress to the gateway.
2. `AuthMiddleware` hashes the key (SHA-256) and looks it up. No key, a wrong key or a revoked key gets 401. If the database is down the answer is 503, so nobody gets in when the check cannot run.
3. The person's role is read from the database on this request. It is never taken from anything the client sends.
4. For `tools/list`, the gateway asks every enabled upstream for its tools, gives each the name `server_tool`, and returns only the tools this role may use.
5. For `tools/call`, the gateway checks the permission first. A refused call is written to the audit log as `denied` and never reaches an upstream.
6. Otherwise the name is split at the first underscore into server and tool, the call goes to that server with that server's own credential (if it has one), and the result is returned in a fresh result object so nothing internal leaks through.
7. The WooCommerce MCP server calls the store's REST API (signed with OAuth 1.0a over HTTP) and returns only what the tool is meant to show (customer name, never email or address).
8. One audit row is written: who, which server and tool, when, how long, and `success`, `tool_error`, `gateway_error` or `denied`. Tool arguments are never stored.

## Aggregation, routing and failure handling

- **Name collisions.** Every tool is exposed as `servername_toolname`, so two servers can both have a `ping` tool (`currency_ping`, `utilities_ping`).
  Server names may not contain an underscore, which keeps the split at the first underscore unambiguous. Server names are unique.
- **Timeouts.** Listing a server's tools gets 5 seconds. A tool call gets 15 seconds. The store client inside the WooCommerce server uses 10 seconds,
  so the store gives up before the gateway does and the AI gets a readable message.
- **A dead upstream.** It is reported as unreachable with the reason ("No answer within 5 seconds.") and skipped. The other servers keep working, and it comes back
  by itself when it answers again, without restarting the gateway. This was tested on the cluster by scaling one server to zero: the dashboard showed
  "2 of 3 connected" while the chat kept answering from the others.
- **Safe errors.** A failure is turned into a short message (`GatewayError`). Stack traces and upstream internals are not sent to clients.
- **Always fresh.** The upstream list and credentials are re-read from the database on each request, so disabling a server or changing an address takes effect at once.
  This costs one small query per request, which is fine at team scale.

## The chat agent

- The dashboard sends the conversation (only `user` and `assistant` messages, so the browser cannot inject system or tool messages) to the admin API.
- The admin API opens an MCP connection to the gateway with a **short-lived delegation token** (two minutes) that names the signed-in person.
  The gateway looks that person up fresh, so the assistant has exactly that person's role, and the audit log shows that person's name.
- The tool loop: ask the model, run the tool calls it asks for through the gateway, add the results, repeat, for at most 6 rounds.
  Results are shortened to 4000 characters. The system prompt tells the model to treat tool descriptions and results as information, never as instructions.
- Calls to the AI provider are retried after 2, 5 and 10 seconds when the provider answers busy (429 or 5xx). The MCP connection allows a long read time because it stays open while the model thinks.
- The conversation lives in the browser. The server keeps no chat history.

## Kubernetes layout

- Namespace `urumi`. Deployments: gateway, admin-api, frontend, three MCP servers, WordPress. StatefulSets: postgres, mariadb. Persistent volume claims for Postgres, MariaDB and WordPress files.
- One Secret (`urumi-secrets`) holds passwords and keys. Pods read it through `secretKeyRef`. Changing it rolls the pods that use it (a checksum annotation on the pod template).
- Public through the Ingress: `/` (dashboard), `/api` (admin API) and `/mcp` (gateway) on one host, and the storefront on a second host. Everything else is a `ClusterIP` service only.
- NetworkPolicies: default deny for incoming traffic in the namespace. The Ingress controller may reach the public services. The MCP servers accept traffic only from the gateway and the admin API.
  Postgres only from the backend and the bootstrap job. MariaDB only from WordPress and the store setup job. WordPress from the WooCommerce MCP server and the store setup job.
  Tested: a pod outside the allow-list timed out (curl exit 28) when it tried to reach the WooCommerce MCP server.
- Requests and limits on every container. Readiness and liveness probes on every service; liveness probes are patient (45 second start delay, six failures) because a laptop cluster is slow to start.
- Containers run as a non-root user (10001) with a read-only root filesystem and a small writable `/tmp`. The service account has no token mounted.
- Jobs: `bootstrap` (creates tables, the first admin and member, registers the three servers) and `store-setup` (installs and configures WooCommerce). Both are post-install hooks.

## What changes for production

| Topic | Local (kind) | Production (k3s on a VPS) |
|---|---|---|
| DNS | `*.localtest.me` resolves to your own computer | real `A` records for the dashboard host and the store host |
| Ingress | ingress-nginx, port 8088 mapped by kind | Traefik (k3s default), standard ports |
| TLS | none | a TLS Secret for both hosts, `scheme: https` |
| Storage class | the cluster default | `local-path` on k3s, or a named class via `storage.storageClass`; bigger sizes |
| Secrets | throw-away defaults in `values.yaml` | generated per install with `--set`, or an `existingSecret` created outside Helm |
| Images | built locally and loaded with `kind load` | imported into k3s or pulled from a registry |
| NetworkPolicy | allows `ingress-nginx` | allows `kube-system` (where Traefik runs); k3s enforces the policies |

The VPS side is described in the README but has not been run yet; the local run exercises the same chart.

## Tradeoffs I chose, and what they cost

- **Audit write failure does not block the call.** If the audit row cannot be written, the call still goes through and a warning is printed. This favours availability. A stricter system would refuse the call; for a compliance setting that would be the right choice.
- **SHA-256 for API keys, not bcrypt.** Keys are 256 bits of random data, so a fast hash is safe and keeps every request cheap. Slow hashes are for short human passwords.
- **Sessions are signed tokens (JWT), but the user is looked up on every request.** Logging out is not instant for the token itself, but a deleted user or a changed role takes effect at once, and a revoked key is refused on the next request.
- **Server list read per request** instead of cached. Simpler and always correct; costs one query. A cache with a short expiry is the next step if load grows.
- **Credentials for upstream servers sit in a database column** and are never returned by the API. They are not encrypted at rest yet; see the threat model for what that means and the fix.
- **One gateway replica.** The gateway keeps no state except the database, but I have not tested MCP sessions across several replicas, so I do not claim that scaling works.
- **Chat rate limit is in memory** (20 messages per ten minutes per person). It resets when the admin API restarts and is per process, so it is a guard for a free AI key, not a security control.
- **No human confirmation for write tools in chat.** An admin's chat can change an order when asked. The audit log records it, but there is no "are you sure" step.
- **Cluster size.** On an 8 GB laptop, Docker needed 5 GB. With 2 GB the cluster's API server timed out, which looked like random failures until I raised the memory limit.
