import { useEffect, useMemo, useState } from "react";
import { api, messageOf, Role, Tool } from "../api";
import { Empty, ErrorBanner, Icon } from "../ui";

type Kind = "all" | "read" | "write";

export default function Tools({ role }: { role: Role }) {
  const [tools, setTools] = useState<Tool[] | null>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [server, setServer] = useState("all");
  const [kind, setKind] = useState<Kind>("all");
  const [open, setOpen] = useState<string | null>(null);

  const load = () => {
    setError("");
    api.tools().then(setTools).catch((problem) => setError(messageOf(problem)));
  };
  useEffect(load, []);

  const servers = useMemo(() => Array.from(new Set(tools?.map((t) => t.server) ?? [])).sort(), [tools]);
  const shown = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    return (tools ?? []).filter(
      (t) =>
        (server === "all" || t.server === server) &&
        (kind === "all" || t.kind === kind) &&
        words.every((w) => (t.full_name + " " + t.description).toLowerCase().includes(w)),
    );
  }, [tools, query, server, kind]);
  const lockedCount = tools?.filter((t) => t.locked).length ?? 0;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Tools</h1>
          <p>
            Every tool the gateway offers, named <code>server_tool</code>.{" "}
            {role === "member" ? "Tools marked admin only are hidden from your key." : "Write tools change the store and need an admin key."}
          </p>
        </div>
        <button className="btn" onClick={load}><Icon name="refresh" size={16} /> Reload</button>
      </div>

      <div className="toolbar">
        <input id="tool-search" className="input" placeholder="Search tools" aria-label="Search tools"
          value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="chips" role="group" aria-label="Filter by server">
          <button className="chip" aria-pressed={server === "all"} onClick={() => setServer("all")}>All servers</button>
          {servers.map((name) => (
            <button key={name} className="chip" aria-pressed={server === name} onClick={() => setServer(name)}>{name}</button>
          ))}
        </div>
        <div className="chips" role="group" aria-label="Filter by type">
          {(["all", "read", "write"] as Kind[]).map((k) => (
            <button key={k} className="chip" aria-pressed={kind === k} onClick={() => setKind(k)}>
              {k === "all" ? "Any type" : k === "read" ? "Read" : "Write"}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorBanner text={error} />}
      {tools && tools.length > 0 && (
        <div className="summary">
          <span><b>{shown.length}</b> of {tools.length} tools{lockedCount > 0 && <> · <b>{lockedCount}</b> admin only</>}</span>
        </div>
      )}
      {tools === null && !error && <div className="grid">{[0, 1, 2, 3].map((i) => <div className="skeleton" key={i} />)}</div>}
      {tools && tools.length === 0 && (
        <Empty title="No tools available">No server is answering right now. Check the Servers page.</Empty>
      )}
      {tools && tools.length > 0 && shown.length === 0 && <Empty title="No tool matches">Try a different word or clear a filter.</Empty>}

      <div className="grid">
        {shown.map((t) => (
          <button key={t.full_name} className={"card tool" + (t.locked ? " locked" : "") + (open === t.full_name ? " open" : "")}
            aria-expanded={open === t.full_name} onClick={() => setOpen(open === t.full_name ? null : t.full_name)}>
            <div className="tool-meta">
              <span className={"pill " + t.kind}>{t.kind === "read" ? "Read" : "Write"}</span>
              {t.locked && <span className="pill denied"><Icon name="lock" size={12} /> Admin only</span>}
              <span className="server-tag">{t.server}</span>
            </div>
            <div className="tool-name">{t.full_name}</div>
            <p className="tool-desc">{t.description || "No description."}</p>
          </button>
        ))}
      </div>
    </>
  );
}
