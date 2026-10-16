import { useCallback, useEffect, useMemo, useState } from "react";
import { api, AuditRow, messageOf, Outcome } from "../api";
import { ago, Empty, ErrorBanner, full, Icon } from "../ui";

const OUTCOMES: { id: Outcome | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "success", label: "Success" },
  { id: "tool_error", label: "Tool error" },
  { id: "gateway_error", label: "Gateway error" },
  { id: "denied", label: "Denied" },
];
const NAMES: Record<Outcome, string> = {
  success: "Success", tool_error: "Tool error", gateway_error: "Gateway error", denied: "Denied",
};

export default function Audit() {
  const [rows, setRows] = useState<AuditRow[] | null>(null);
  const [error, setError] = useState("");
  const [outcome, setOutcome] = useState<Outcome | "all">("all");
  const [query, setQuery] = useState("");

  const load = useCallback(() => {
    api.audit(300).then((data) => { setRows(data); setError(""); }).catch((problem) => setError(messageOf(problem)));
  }, []);
  useEffect(load, [load]);

  const shown = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    return (rows ?? []).filter(
      (r) =>
        (outcome === "all" || r.outcome === outcome) &&
        words.every((w) => `${r.user_name ?? ""} ${r.upstream} ${r.tool}`.toLowerCase().includes(w)),
    );
  }, [rows, outcome, query]);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Audit log</h1>
          <p>Who called which tool, how long it took and how it ended. Tool arguments are never stored, so customer data stays out of the log.</p>
        </div>
        <button className="btn" onClick={load}><Icon name="refresh" size={16} /> Reload</button>
      </div>

      <div className="toolbar">
        <input id="audit-search" className="input" placeholder="Filter by person, server or tool" aria-label="Filter the log"
          value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="chips" role="group" aria-label="Filter by outcome">
          {OUTCOMES.map((o) => (
            <button key={o.id} className="chip" aria-pressed={outcome === o.id} onClick={() => setOutcome(o.id)}>{o.label}</button>
          ))}
        </div>
      </div>

      {error && <ErrorBanner text={error} />}
      {rows === null && !error && <div className="skeleton" style={{ minHeight: 260 }} />}
      {rows && rows.length === 0 && <Empty title="Nothing logged yet">Calls through the gateway will appear here.</Empty>}
      {rows && rows.length > 0 && shown.length === 0 && <Empty title="No entry matches">Try a different word or outcome.</Empty>}
      {shown.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>When</th><th>Person</th><th>Tool</th><th>Outcome</th><th className="num">Time</th></tr>
            </thead>
            <tbody>
              {shown.map((r) => (
                <tr key={r.id}>
                  <td className="muted" title={full(r.created_at)}>{ago(r.created_at)}</td>
                  <td>{r.user_name ?? <span className="muted">deleted user</span>}</td>
                  <td><code>{r.upstream}_{r.tool}</code></td>
                  <td><span className={"pill " + r.outcome}>{NAMES[r.outcome]}</span></td>
                  <td className="num">{r.duration_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
