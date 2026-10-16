import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { api, messageOf, ServerHealth } from "../api";
import { ConfirmButton, Empty, ErrorBanner, Icon, Sparkline, useToast } from "../ui";

const REFRESH_MS = 15000;
const HISTORY = 24;

function AddServer({ onAdded }: { onAdded: () => void }) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [credential, setCredential] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.addServer(name.trim(), url.trim(), credential);
      toast(`Server "${name.trim()}" added.`);
      setName(""); setUrl(""); setCredential("");
      onAdded();
    } catch (problem) {
      setError(messageOf(problem));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel" onSubmit={submit} style={{ marginBottom: 18, display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="form-row">
        <div className="field">
          <label htmlFor="server-name">Name</label>
          <input id="server-name" className="input mono" value={name} placeholder="inventory"
            onChange={(e) => setName(e.target.value.toLowerCase())} />
          <span className="hint">Lower-case letters and digits only.</span>
        </div>
        <div className="field">
          <label htmlFor="server-url">Address</label>
          <input id="server-url" className="input mono" value={url} placeholder="https://tools.example.com/mcp"
            onChange={(e) => setUrl(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="server-credential">Credential (optional)</label>
          <input id="server-credential" className="input mono" type="password" autoComplete="off" value={credential}
            onChange={(e) => setCredential(e.target.value)} />
        </div>
        <button className="btn primary" disabled={busy || !name.trim() || !url.trim()}>
          <Icon name="plus" size={16} /> {busy ? "Adding…" : "Add server"}
        </button>
      </div>
      {error && <div className="error-text" role="alert">{error}</div>}
    </form>
  );
}

function EditServer({ server, onDone }: { server: ServerHealth; onDone: () => void }) {
  const [url, setUrl] = useState(server.url);
  const [credential, setCredential] = useState("");
  const [removeCredential, setRemoveCredential] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    // Blank keeps the saved credential. The checkbox removes it. Anything typed replaces it.
    const sent = removeCredential ? "" : credential === "" ? null : credential;
    try {
      await api.editServer(server.id, url.trim(), sent);
      toast(`${server.name} updated.`);
      onDone();
    } catch (problem) {
      setError(messageOf(problem));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div className="field">
        <label htmlFor={`edit-url-${server.id}`}>Address</label>
        <input id={`edit-url-${server.id}`} className="input mono" value={url} onChange={(e) => setUrl(e.target.value)} />
      </div>
      <div className="field">
        <label htmlFor={`edit-cred-${server.id}`}>New credential</label>
        <input id={`edit-cred-${server.id}`} className="input mono" type="password" autoComplete="off"
          value={credential} disabled={removeCredential} onChange={(e) => setCredential(e.target.value)} />
        <span className="hint">{server.has_credential ? "A credential is saved. Leave blank to keep it." : "No credential is saved."}</span>
      </div>
      {server.has_credential && (
        <label style={{ display: "inline-flex", gap: 8, alignItems: "center", fontSize: 13 }}>
          <input type="checkbox" checked={removeCredential} onChange={(e) => setRemoveCredential(e.target.checked)} />
          Remove the saved credential
        </label>
      )}
      {error && <div className="error-text" role="alert">{error}</div>}
      <div style={{ display: "flex", gap: 8 }}>
        <button className="btn primary small" disabled={busy || !url.trim()}>{busy ? "Saving…" : "Save"}</button>
        <button type="button" className="btn small" onClick={onDone}>Cancel</button>
      </div>
    </form>
  );
}

function ServerCard({ server, history, onChanged }: { server: ServerHealth; history: number[]; onChanged: () => void }) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);

  async function run(action: () => Promise<unknown>, done: string) {
    setBusy(true);
    try { await action(); toast(done); onChanged(); }
    catch (problem) { toast(messageOf(problem), true); }
    finally { setBusy(false); }
  }

  const label = server.status === "up" ? "Connected" : server.status === "down" ? "Unreachable" : "Disabled";
  return (
    <article className={"card" + (server.status === "down" ? " is-down" : "") + (server.status === "disabled" ? " is-off" : "")}>
      <div className="card-top">
        <div className="card-name">
          <span className={"dot " + (server.status === "disabled" ? "" : server.status)} aria-hidden="true" />
          {server.name}
        </div>
        <span className="muted" style={{ fontSize: 13 }}>{label}</span>
      </div>
      {editing && <EditServer server={server} onDone={() => { setEditing(false); onChanged(); }} />}
      {!editing && <code className="card-url">{server.url}</code>}
      {server.status === "down" && <div className="error-text">{server.error}</div>}
      <div className="stats">
        <div className="stat"><b>{server.latency_ms === null ? "–" : `${server.latency_ms} ms`}</b><span>Response time</span></div>
        <div className="stat"><b>{server.tool_count ?? "–"}</b><span>Tools</span></div>
      </div>
      <Sparkline values={history} />
      <div className="card-foot">
        <label style={{ display: "inline-flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
          <span className="switch">
            <input type="checkbox" checked={server.enabled} disabled={busy}
              aria-label={`${server.enabled ? "Switch off" : "Switch on"} ${server.name}`}
              onChange={(e) => run(() => api.setServerEnabled(server.id, e.target.checked),
                e.target.checked ? `${server.name} switched on.` : `${server.name} switched off.`)} />
            <span />
          </span>
          <span className="muted" style={{ fontSize: 13 }}>{server.enabled ? "On" : "Off"}</span>
        </label>
        <button className="btn small" onClick={() => setEditing((open) => !open)} disabled={busy}>
          {editing ? "Close" : "Edit"}
        </button>
        <ConfirmButton label="Remove" confirmLabel="Click to confirm" disabled={busy}
          onConfirm={() => run(() => api.removeServer(server.id), `${server.name} removed.`)} />
      </div>
    </article>
  );
}

export default function Servers() {
  const [rows, setRows] = useState<ServerHealth[] | null>(null);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const history = useRef<Record<string, number[]>>({});

  const load = useCallback(async () => {
    try {
      const data = await api.health();
      for (const server of data) {
        if (server.latency_ms !== null && server.status === "up") {
          const list = history.current[server.name] ?? [];
          history.current[server.name] = [...list, server.latency_ms].slice(-HISTORY);
        }
      }
      setRows(data);
      setError("");
    } catch (problem) {
      setError(messageOf(problem));
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => clearInterval(timer);
  }, [load]);

  const active = rows?.filter((r) => r.enabled) ?? [];
  const answering = active.filter((r) => r.status === "up").length;
  const toolTotal = rows?.reduce((sum, r) => sum + (r.tool_count ?? 0), 0) ?? 0;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Servers</h1>
          <p>The tool servers behind the gateway. Each one is checked every {REFRESH_MS / 1000} seconds while this page is open.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={load}><Icon name="refresh" size={16} /> Check now</button>
          <button className="btn primary" onClick={() => setShowAdd((open) => !open)}>
            <Icon name="plus" size={16} /> {showAdd ? "Close" : "Add server"}
          </button>
        </div>
      </div>

      {showAdd && <AddServer onAdded={load} />}
      {error && <ErrorBanner text={error} />}

      {rows && rows.length > 0 && (
        <div className="summary">
          <span className={"dot " + (answering === active.length ? "up" : "down")} aria-hidden="true" />
          <span><b>{answering} of {active.length}</b> active servers connected · <b>{toolTotal}</b> tools available</span>
        </div>
      )}

      {rows === null && !error && (
        <div className="grid">{[0, 1, 2].map((i) => <div className="skeleton" key={i} />)}</div>
      )}
      {rows && rows.length === 0 && (
        <Empty title="No servers yet">Use "Add server" to connect the first tool server.</Empty>
      )}
      {rows && rows.length > 0 && (
        <div className="grid">
          {rows.map((server) => (
            <ServerCard key={server.id} server={server} history={history.current[server.name] ?? []} onChanged={load} />
          ))}
        </div>
      )}
    </>
  );
}
