import { FormEvent, useState } from "react";
import { api, messageOf, setToken, User } from "../api";
import { Logo } from "../ui";

export default function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { token, user } = await api.login(key.trim());
      setToken(token);
      onLogin(user);
    } catch (problem) {
      setError(messageOf(problem));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <svg className="blade" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
        <path d="M-40 640 C 220 640, 260 180, 520 180 S 820 700, 1240 560" />
        <path d="M-40 700 C 260 700, 300 260, 560 260 S 880 740, 1240 640" />
        <path d="M-40 760 C 300 760, 340 340, 600 340 S 940 780, 1240 720" />
      </svg>
      <form className="panel login-card" onSubmit={submit}>
        <Logo size={44} />
        <div>
          <h1>Urumi Gateway</h1>
          <p>Sign in with your gateway API key to manage servers, tools and access.</p>
        </div>
        <div className="field">
          <label htmlFor="api-key">API key</label>
          <input
            id="api-key" className="input mono" type="password" autoComplete="off" spellCheck={false}
            placeholder="urumi_…" value={key} onChange={(e) => setKey(e.target.value)} autoFocus
          />
          <span className="hint">The key is sent once to sign you in and is never stored by this page.</span>
        </div>
        {error && <div className="error-text" role="alert">{error}</div>}
        <button className="btn primary" disabled={busy || key.trim().length === 0}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
