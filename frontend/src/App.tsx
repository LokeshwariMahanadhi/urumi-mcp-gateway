import { useCallback, useEffect, useMemo, useState } from "react";
import { api, hasToken, setToken, User, whenSessionEnds } from "./api";
import { Icon, Logo, ToastProvider, useToast } from "./ui";
import Palette, { PaletteItem } from "./Palette";
import Login from "./pages/Login";
import Servers from "./pages/Servers";
import Tools from "./pages/Tools";
import Chat from "./pages/Chat";
import Keys from "./pages/Keys";
import MyKeys from "./pages/MyKeys";
import Audit from "./pages/Audit";

type PageId = "servers" | "tools" | "chat" | "keys" | "audit";
const PAGES: { id: PageId; label: string; icon: string; adminOnly: boolean }[] = [
  { id: "servers", label: "Servers", icon: "servers", adminOnly: true },
  { id: "tools", label: "Tools", icon: "tools", adminOnly: false },
  { id: "chat", label: "Chat", icon: "chat", adminOnly: false },
  { id: "keys", label: "Keys", icon: "keys", adminOnly: false },
  { id: "audit", label: "Audit log", icon: "audit", adminOnly: true },
];

type Theme = "dark" | "light" | "system";
function readTheme(): Theme {
  try {
    const saved = localStorage.getItem("urumi-theme");
    if (saved === "dark" || saved === "light") return saved;
  } catch { /* storage blocked: fall back to the system setting */ }
  return "system";
}

function Shell({ user, onSignOut, theme, toggleTheme }: {
  user: User; onSignOut: () => void; theme: Theme; toggleTheme: () => void;
}) {
  const allowed = useMemo(() => PAGES.filter((p) => user.role === "admin" || !p.adminOnly), [user.role]);
  const fromHash = () => {
    const wanted = window.location.hash.replace("#", "");
    return allowed.find((p) => p.id === wanted)?.id ?? allowed[0].id;
  };
  const [page, setPage] = useState<PageId>(fromHash);
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    const onHash = () => setPage(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  });
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const go = useCallback((id: PageId) => { window.location.hash = id; setPage(id); }, []);
  const items: PaletteItem[] = [
    ...allowed.map((p) => ({ label: `Go to ${p.label}`, hint: "Page", run: () => go(p.id) })),
    { label: "Switch light or dark theme", hint: "Action", run: toggleTheme },
    { label: "Sign out", hint: "Action", run: onSignOut },
  ];

  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <Logo />
          <div>
            <div className="brand-name">Urumi Gateway</div>
            <div className="brand-sub">MCP control room</div>
          </div>
        </div>
        <nav className="nav" aria-label="Main">
          {allowed.map((p) => (
            <button key={p.id} aria-current={page === p.id ? "page" : undefined} onClick={() => go(p.id)}>
              <Icon name={p.icon} /> {p.label}
            </button>
          ))}
        </nav>
        <div className="side-foot">
          <div className="who">
            <b>{user.name}</b>
            <span>{user.role === "admin" ? "Administrator" : "Team member"}</span>
          </div>
        </div>
      </aside>

      <div className="main">
        <div className="topbar">
          <button className="cmdk" onClick={() => setPaletteOpen(true)} aria-label="Open command palette">
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}><Icon name="search" size={16} /> Jump to…</span>
            <kbd>Ctrl K</kbd>
          </button>
          <div className="topbar-actions">
            <button className="btn icon-btn" onClick={toggleTheme} aria-label="Switch light or dark theme" title="Switch theme">
              <Icon name={theme === "light" ? "moon" : "sun"} />
            </button>
            <button className="btn icon-btn" onClick={onSignOut} aria-label="Sign out" title="Sign out">
              <Icon name="out" />
            </button>
          </div>
        </div>
        <main className="page">
          {page === "servers" && <Servers />}
          {page === "tools" && <Tools role={user.role} />}
          {page === "chat" && <Chat />}
          {page === "keys" && (user.role === "admin" ? <Keys /> : <MyKeys />)}
          {page === "audit" && <Audit />}
        </main>
      </div>
      {paletteOpen && <Palette items={items} onClose={() => setPaletteOpen(false)} />}
    </div>
  );
}

function Root() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(hasToken());
  const [theme, setTheme] = useState<Theme>(readTheme);
  const toast = useToast();

  const signOut = useCallback(() => { setToken(null); setUser(null); }, []);

  useEffect(() => {
    whenSessionEnds(() => { setUser(null); toast("Your session ended. Please sign in again.", true); });
    if (!hasToken()) return;
    api.me().then(setUser).catch(() => setToken(null)).finally(() => setChecking(false));
  }, [toast]);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    const isDark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    const next: Theme = isDark ? "light" : "dark";
    setTheme(next);
    try { localStorage.setItem("urumi-theme", next); } catch { /* not saved, still applied */ }
  };

  if (checking) return null;
  if (!user) return <Login onLogin={setUser} />;
  return <Shell user={user} onSignOut={signOut} theme={theme} toggleTheme={toggleTheme} />;
}

export default function App() {
  return (
    <ToastProvider>
      <Root />
    </ToastProvider>
  );
}
