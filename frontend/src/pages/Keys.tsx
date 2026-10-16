import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, KeyRow, messageOf, Role, UserRow } from "../api";
import { ago, ConfirmButton, Empty, ErrorBanner, full, Icon, useToast } from "../ui";

export default function Keys() {
  const [keys, setKeys] = useState<KeyRow[] | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [error, setError] = useState("");
  const [userId, setUserId] = useState("");
  const [label, setLabel] = useState("");
  const [fresh, setFresh] = useState<{ key: string; owner: string } | null>(null);
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState<Role>("member");
  const toast = useToast();

  const load = useCallback(async () => {
    try {
      const [k, u] = await Promise.all([api.keys(), api.users()]);
      setKeys(k);
      setUsers(u);
      setError("");
      setUserId((current) => current || String(u[0]?.id ?? ""));
    } catch (problem) {
      setError(messageOf(problem));
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function createKey(event: FormEvent) {
    event.preventDefault();
    try {
      const { key } = await api.newKey(Number(userId), label.trim());
      setFresh({ key, owner: users.find((u) => u.id === Number(userId))?.name ?? "" });
      setLabel("");
      load();
    } catch (problem) {
      toast(messageOf(problem), true);
    }
  }

  async function addUser(event: FormEvent) {
    event.preventDefault();
    try {
      await api.addUser(newEmail.trim(), newName.trim(), newRole);
      toast(`${newName.trim()} added.`);
      setNewEmail(""); setNewName("");
      load();
    } catch (problem) {
      toast(messageOf(problem), true);
    }
  }

  async function revoke(row: KeyRow) {
    try { await api.revokeKey(row.id); toast("Key revoked."); load(); }
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
          <h1>Keys and people</h1>
          <p>Each person signs in with their own key. Keys are stored as one-way hashes, so a key can be shown only once, when it is created.</p>
        </div>
      </div>

      {error && <ErrorBanner text={error} />}

      {fresh && (
        <div className="panel reveal" role="alert">
          <div><b>New key for {fresh.owner}.</b> Copy it now. It cannot be shown again.</div>
          <div className="secret">
            <code>{fresh.key}</code>
            <button className="btn" onClick={() => copy(fresh.key)}><Icon name="copy" size={16} /> Copy</button>
          </div>
          <div><button className="btn small" onClick={() => setFresh(null)}>I have copied it</button></div>
        </div>
      )}

      <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", marginBottom: 22 }}>
        <form className="panel" onSubmit={createKey} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <h3>Create a key</h3>
          <div className="field">
            <label htmlFor="key-user">Person</label>
            <select id="key-user" className="input" value={userId} onChange={(e) => setUserId(e.target.value)}>
              {users.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.role})</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="key-label">Label (optional)</label>
            <input id="key-label" className="input" value={label} placeholder="Laptop, CI, Claude Desktop…" onChange={(e) => setLabel(e.target.value)} />
          </div>
          <button className="btn primary" disabled={!userId}>Create key</button>
        </form>

        <form className="panel" onSubmit={addUser} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <h3>Add a person</h3>
          <div className="field">
            <label htmlFor="user-name">Name</label>
            <input id="user-name" className="input" value={newName} onChange={(e) => setNewName(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="user-email">Email</label>
            <input id="user-email" className="input" type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="user-role">Role</label>
            <select id="user-role" className="input" value={newRole} onChange={(e) => setNewRole(e.target.value as Role)}>
              <option value="member">Member: read tools only</option>
              <option value="admin">Admin: everything</option>
            </select>
          </div>
          <button className="btn" disabled={!newName.trim() || !newEmail.trim()}>Add person</button>
        </form>
      </div>

      {keys && keys.length === 0 && <Empty title="No keys yet">Create the first key above.</Empty>}
      {keys && keys.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Person</th><th>Label</th><th>Key starts with</th><th>Created</th><th>Status</th><th /></tr>
            </thead>
            <tbody>
              {[...keys].reverse().map((k) => (
                <tr key={k.id}>
                  <td>{k.user_name}</td>
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
