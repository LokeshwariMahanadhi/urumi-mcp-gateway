# Security notes

What the gateway does today. The reasoning about attackers is in [`THREAT_MODEL.md`](THREAT_MODEL.md).

## Who can do what

| | Admin | Member |
|---|---|---|
| See and call read tools (list products, list orders, get order, currency, utilities) | Yes | Yes |
| See and call write tools (`woocommerce_create_product`, `woocommerce_update_order_status`) | Yes | No |
| Dashboard: servers, all keys, users, audit log | Yes | No |
| Dashboard: tools, chat, their own keys | Yes | Yes |

The role is read from the database on every request. It never comes from anything the client sends.
A member does not see the write tools, and if a member calls one by name anyway, the gateway refuses
before any upstream server is contacted (written to the audit log as `denied`). Both are enforced on the server.

## API keys

- A key looks like `urumi_...` and is made with Python's `secrets` module (256 bits of randomness).
- The database stores only a SHA-256 hash and the first 12 characters (so people can tell keys apart).
  The full key is shown once when it is created and cannot be read again.
- A key is revoked by setting `revoked_at`. A revoked key is refused on the next request.
- SHA-256 is fine here because the keys are long and random. A slow hash such as bcrypt is meant for short, guessable human passwords.

## The key check

Every request to `/mcp` passes through `AuthMiddleware` first.

- No key: 401. Wrong or revoked key: 401.
- If the database cannot be reached, the answer is 503. Nobody gets in when the check cannot run.
- The MCP endpoint only accepts requests addressed to its own host names (DNS-rebinding guard). In Kubernetes the allowed names are set with `ALLOWED_MCP_HOSTS`.

## Dashboard sign-in

The dashboard signs in with an API key and gets a signed session token. On every request the person is looked up again, so a revoked key,
a deleted user or a changed role takes effect immediately.

## Audit log

Every tool call writes one row: who, which server, which tool, when, how long, and the outcome
(`success`, `tool_error`, `gateway_error` or `denied`). Refused attempts are logged too.
Tool arguments are not stored, because they can contain customer details.
If writing the log fails, the call still goes through and a warning is printed. A stricter design would refuse the call; this is a deliberate trade-off.
Changes to keys, users and servers are not audited yet.

## Upstream servers

- Only admins can add or edit servers. The address must be `http` or `https`, must have no user name or password, and must resolve only to public
  addresses. The operator can approve internal host names with `ALLOWED_UPSTREAM_HOSTS` (the chart approves its own three services).
- Each saved credential is sent only to its own server. Client tokens are never forwarded.
- Credentials are not encrypted at rest yet.

## Kubernetes

- Passwords and keys are in one Kubernetes Secret, read through `secretKeyRef`. Nothing secret is in the images or in `values-local.yaml`.
- NetworkPolicies deny incoming traffic by default and allow only the paths that are needed. The MCP servers and databases are not public.
- Containers run as a non-root user with a read-only root filesystem. The service account has no token.

## The chat agent

- Acts as the signed-in person through a two-minute delegation token. It cannot do more than that person.
- The system prompt treats tool descriptions and tool results as information only. Results are cut to 4000 characters and a chat does at most 6 tool rounds.
- At most 20 messages per person per ten minutes.

## Not built yet

- Upstream credentials encrypted at rest.
- Audit entries for key, user and server changes.
- Per-key rate limits on `/mcp`.
- Egress network rules, and a re-check of an upstream address when connecting (DNS rebinding).
- Pinned tool descriptions, and a confirmation step before write tools in chat.
