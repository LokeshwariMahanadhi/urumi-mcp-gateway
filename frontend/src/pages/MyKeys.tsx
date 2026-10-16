import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, messageOf, MyKeyRow } from "../api";
import { ago, ConfirmButton, Empty, ErrorBanner, full, Icon, useToast } from "../ui";

// What a team member sees: only their own keys.
export default function MyKeys() {
  const [keys, setKeys] = useState<MyKeyRow[] | null>(null);
  const [error, setError] = useState("");
  const [label, setLabel] = useState("");
  const [fresh, setFresh] = useState<string | null>(null);
  const toast = useToast();

  const load = useCallback(async () => {
    try {
      setKeys(await api.myKeys());
      setError("");
    } catch (problem) {
      setError(messageOf(problem));
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function createKey(event: FormEvent) {
    event.preventDefault();
    try {
      const { key } = await api.newMyKey(label.trim());
      setFresh(key);
      setLabel("");
      load();
    } catch (problem) {
      toast(messageOf(problem), true);
    }
  }

  async function revoke(row: MyKeyRow) {
    try { await api.revokeMyKey(row.id); toast("Key revoked."); load(); }
    catch (problem) { toast(messageOf(problem), true); }
  }

  async function copy(text: string) {
    try { await navigator.clipboard.writeText(text); toast("Copied."); }
    catch { toast("Could not copy. Select the key and copy it by hand.", true); }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My keys</h1>
          <p>Use a key with the gateway address in Claude Code, Cursor or MCP Inspector. A key is shown only once, when you create it.</p>
        </div>
      </div>

      {error && <ErrorBanner text={error} />}

      {fresh && (
        <div className="panel reveal" role="alert">
          <div><b>Your new key.</b> Copy it now. It cannot be shown again.</div>
          <div className="secret">
            <code>{fresh}</code>
            <button className="btn" onClick={() => copy(fresh)}><Icon name="copy" size={16} /> Copy</button>
          </div>
          <div><button className="btn small" onClick={() => setFresh(null)}>I have copied it</button></div>
        </div>
      )}

      <form className="panel" onSubmit={createKey} style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 420, marginBottom: 22 }}>
        <h3>Create a key</h3>
        <div className="field">
          <label htmlFor="my-key-label">Label (optional)</label>
          <input id="my-key-label" className="input" value={label} placeholder="Laptop, Cursor, Claude Code…" onChange={(e) => setLabel(e.target.value)} />
        </div>
        <button className="btn primary">Create key</button>
      </form>

      {keys && keys.length === 0 && <Empty title="No keys yet">Create your first key above.</Empty>}
      {keys && keys.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Label</th><th>Key starts with</th><th>Created</th><th>Status</th><th /></tr>
            </thead>
            <tbody>
              {[...keys].reverse().map((k) => (
                <tr key={k.id}>
                  <td className="muted">{k.label || "–"}</td>
                  <td><code>{k.key_prefix}…</code></td>
                  <td className="muted" title={full(k.created_at)}>{ago(k.created_at)}</td>
                  <td><span className={"pill " + (k.revoked_at ? "revoked" : "active")}>{k.revoked_at ? "Revoked" : "Active"}</span></td>
                  <td className="num">{!k.revoked_at && <ConfirmButton label="Revoke" confirmLabel="Click to confirm" onConfirm={() => revoke(k)} />}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
