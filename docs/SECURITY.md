\# Security notes



This file describes what the gateway does today. It grows as the project grows.



\## Who can do what



| | Admin | Member |

|---|---|---|

| See and call read tools (list products, list orders, currency, utilities) | Yes | Yes |

| See and call write tools (`woocommerce\_create\_product`, `woocommerce\_update\_order\_status`) | Yes | No |



The role is read from the database on every request. It never comes from anything the client sends.

A member cannot see the write tools, and if a member calls one by name anyway, the gateway refuses

before the upstream server is contacted. Both are enforced on the server.



\## API keys



\- A key looks like `urumi\_...` and is made with Python's `secrets` module (256 bits of randomness).

\- The database stores only a SHA-256 hash and the first 12 characters (so people can tell keys apart).

&#x20; The full key is shown once when it is created and cannot be read again.

\- A key is revoked by setting `revoked\_at`. A revoked key is refused on the next request.

\- SHA-256 is fine here because the keys are long and random. A slow hash such as bcrypt is meant for

&#x20; short, guessable human passwords.



\## The key check



Every request to `/mcp` passes through `AuthMiddleware` first.



\- No key: 401. Wrong or revoked key: 401.

\- If the database cannot be reached, the answer is 503. Nobody gets in when the check cannot run.



\## Audit log



Every tool call writes one row: who, which server, which tool, when, how long, and the outcome

(`success`, `tool\_error`, `gateway\_error` or `denied`). Refused attempts are logged too.

Tool arguments are not stored, because they can contain customer details.

If writing the log fails, the call still goes through and a warning is printed.

A stricter design would refuse the call instead. This is a deliberate trade-off.



\## Not built yet (planned)



\- Upstream credentials stored encrypted, and never passed through to clients.

\- Client tokens are never forwarded to upstream servers.

\- Checking the URL when an admin adds an upstream server (to block requests to internal addresses).

\- Kubernetes network rules, non-root containers and secrets handling.

\- Treating upstream tool descriptions as untrusted text (prompt-injection risk) in the chat agent.

