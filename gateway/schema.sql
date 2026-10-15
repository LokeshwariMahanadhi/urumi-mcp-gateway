-- People who can use the gateway. The role is enforced on the server.
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('admin', 'member')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Each user can have several keys. We store only a hash, never the key itself.
-- key_prefix is the first few characters, so people can tell their keys apart.
-- A key is revoked by setting revoked_at.
CREATE TABLE IF NOT EXISTS api_keys (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label       TEXT NOT NULL DEFAULT '',
    key_prefix  TEXT NOT NULL,
    key_hash    TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at  TIMESTAMPTZ
);

-- The upstream MCP servers an admin has registered.
-- The name has no underscore, because "_" joins the server and tool names.
CREATE TABLE IF NOT EXISTS upstream_servers (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL CHECK (name ~ '^[a-z0-9]+$'),
    url         TEXT NOT NULL,
    credential  TEXT,
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row for every tool call. user_name is copied in, so the log still
-- makes sense if the user is deleted later.
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name   TEXT NOT NULL,
    upstream    TEXT NOT NULL,
    tool        TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    outcome     TEXT NOT NULL CHECK (outcome IN ('success', 'tool_error', 'gateway_error', 'denied'))
);