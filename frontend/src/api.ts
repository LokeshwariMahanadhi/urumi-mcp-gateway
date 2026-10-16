// Everything the dashboard asks the admin API goes through this file.

export type Role = "admin" | "member";
export interface User { id: number; name: string; email: string; role: Role }
export interface ServerHealth {
  id: number; name: string; url: string; enabled: boolean; has_credential: boolean;
  status: "up" | "down" | "disabled"; latency_ms: number | null; tool_count: number | null; error: string;
}
export interface Tool {
  server: string; name: string; full_name: string; description: string; kind: "read" | "write"; locked: boolean;
}
export interface KeyRow {
  id: number; user_id: number; user_name: string; label: string; key_prefix: string;
  created_at: string; revoked_at: string | null;
}
export interface MyKeyRow {
  id: number; label: string; key_prefix: string; created_at: string; revoked_at: string | null;
}
export interface UserRow extends User { created_at: string }
export type Outcome = "success" | "tool_error" | "gateway_error" | "denied";
export interface AuditRow {
  id: number; created_at: string; user_name: string | null; upstream: string; tool: string;
  duration_ms: number; outcome: Outcome;
}

const BASE: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8300";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// The session token lives in sessionStorage: it is gone when the tab closes.
let token: string | null = null;
try { token = sessionStorage.getItem("urumi-token"); } catch { token = null; }
let onSessionEnded: () => void = () => {};

export function setToken(value: string | null) {
  token = value;
  try {
    if (value) sessionStorage.setItem("urumi-token", value);
    else sessionStorage.removeItem("urumi-token");
  } catch { /* storage may be blocked; the app still works until reload */ }
}
export const hasToken = () => token !== null;
export function whenSessionEnds(handler: () => void) { onSessionEnded = handler; }

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let reply: Response;
  try {
    reply = await fetch(BASE + path, {
      method,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, `Cannot reach the admin API at ${BASE}. Is it running?`);
  }
  if (!reply.ok) {
    let message = `Request failed (${reply.status}).`;
    try {
      const data = await reply.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = "Please check the values you entered.";
    } catch { /* keep the generic message */ }
    if (reply.status === 401 && token) { setToken(null); onSessionEnded(); }
    throw new ApiError(reply.status, message);
  }
  return reply.json() as Promise<T>;
}

export const api = {
  login: (apiKey: string) => request<{ token: string; user: User }>("POST", "/api/login", { api_key: apiKey }),
  me: () => request<User>("GET", "/api/me"),
  health: () => request<ServerHealth[]>("GET", "/api/servers/health"),
  tools: () => request<Tool[]>("GET", "/api/tools"),
  addServer: (name: string, url: string, credential: string) =>
    request<{ id: number }>("POST", "/api/servers", { name, url, credential }),
  setServerEnabled: (id: number, enabled: boolean) =>
    request<{ enabled: boolean }>("POST", `/api/servers/${id}/enabled`, { enabled }),
  editServer: (id: number, url: string, credential: string | null) =>
    request<{ updated: boolean }>("PUT", `/api/servers/${id}`, { url, credential }),
  removeServer: (id: number) => request<{ deleted: boolean }>("DELETE", `/api/servers/${id}`),
  users: () => request<UserRow[]>("GET", "/api/users"),
  addUser: (email: string, name: string, role: Role) =>
    request<{ id: number }>("POST", "/api/users", { email, name, role }),
  keys: () => request<KeyRow[]>("GET", "/api/keys"),
  newKey: (userId: number, label: string) =>
    request<{ key: string }>("POST", `/api/users/${userId}/keys`, { label }),
  revokeKey: (id: number) => request<{ revoked: boolean }>("POST", `/api/keys/${id}/revoke`),
  myKeys: () => request<MyKeyRow[]>("GET", "/api/me/keys"),
  newMyKey: (label: string) => request<{ key: string }>("POST", "/api/me/keys", { label }),
  revokeMyKey: (id: number) => request<{ revoked: boolean }>("POST", `/api/me/keys/${id}/revoke`),
  audit: (limit = 200) => request<AuditRow[]>("GET", `/api/audit?limit=${limit}`),
};

export const messageOf = (error: unknown) => (error instanceof Error ? error.message : "Something went wrong.");
