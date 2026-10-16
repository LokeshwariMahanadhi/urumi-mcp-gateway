// Small shared building blocks.
import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from "react";

// ---------- icons ----------
const ICONS: Record<string, string> = {
  servers: "M4 6h16M4 12h16M4 18h16M7 6v0M7 12v0M7 18v0",
  tools: "M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.4 2.4-2.6-.6-.6-2.6z",
  keys: "M15 7a4 4 0 1 1-3.5 5.9L4 20v-3l2-2v-2h2l3.5-3.5A4 4 0 0 1 15 7z",
  audit: "M5 4h14v16H5zM9 9h6M9 13h6M9 17h3",
  sun: "M12 4V2m0 20v-2m8-8h2M2 12h2m13.7-5.7 1.4-1.4M4.9 19.1l1.4-1.4m0-11.4L4.9 4.9m14.2 14.2-1.4-1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
  moon: "M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z",
  refresh: "M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7",
  out: "M10 4H5v16h5M15 8l4 4-4 4M19 12H9",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-5-5",
  lock: "M7 11V8a5 5 0 0 1 10 0v3M6 11h12v9H6z",
  copy: "M9 9h11v11H9zM5 15V4h11",
  plus: "M12 5v14M5 12h14",
  chat: "M4 5h16v11H9l-5 4zM8 9h8M8 12h5",
};
export function Icon({ name, size = 18 }: { name: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}

export function Logo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#0B1220" />
      <path d="M5 23c5 0 5-14 10-14s5 14 10 14" fill="none" stroke="#19E6D0" strokeWidth="3" strokeLinecap="round" />
      <path d="M25 23l3-5-6 1z" fill="#19E6D0" />
    </svg>
  );
}

// ---------- toasts ----------
interface ToastItem { id: number; text: string; bad: boolean }
const ToastContext = createContext<(text: string, bad?: boolean) => void>(() => {});
export const useToast = () => useContext(ToastContext);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const counter = useRef(0);
  const show = useCallback((text: string, bad = false) => {
    const id = ++counter.current;
    setItems((current) => [...current, { id, text, bad }]);
    setTimeout(() => setItems((current) => current.filter((item) => item.id !== id)), 4500);
  }, []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {items.map((item) => (
          <div key={item.id} className={"toast" + (item.bad ? " bad" : "")}>{item.text}</div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// ---------- confirm-on-second-click button ----------
export function ConfirmButton({ label, confirmLabel, onConfirm, disabled }: {
  label: string; confirmLabel: string; onConfirm: () => void; disabled?: boolean;
}) {
  const [armed, setArmed] = useState(false);
  useEffect(() => {
    if (!armed) return;
    const timer = setTimeout(() => setArmed(false), 4000);
    return () => clearTimeout(timer);
  }, [armed]);
  return (
    <button
      type="button"
      className={"btn small danger" + (armed ? " armed" : "")}
      disabled={disabled}
      onClick={() => { if (armed) { setArmed(false); onConfirm(); } else setArmed(true); }}
    >
      {armed ? confirmLabel : label}
    </button>
  );
}

// ---------- empty state, banner ----------
export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="empty panel">
      <h3>{title}</h3>
      <div>{children}</div>
    </div>
  );
}
export const ErrorBanner = ({ text }: { text: string }) => <div className="banner" role="alert">{text}</div>;

// ---------- sparkline ----------
export function Sparkline({ values }: { values: number[] }) {
  const width = 240, height = 34, pad = 4;
  if (values.length === 0) return <svg className="spark" viewBox={`0 0 ${width} ${height}`} />;
  const low = Math.min(...values), high = Math.max(...values);
  const span = high - low || 1;
  const x = (i: number) => (values.length === 1 ? width - pad : pad + (i * (width - pad * 2)) / (values.length - 1));
  const y = (v: number) => height - pad - ((v - low) / span) * (height - pad * 2);
  const points = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const last = values.length - 1;
  return (
    <svg className="spark" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img"
      aria-label={`Response time over the last ${values.length} checks, latest ${values[last]} milliseconds`}>
      <polyline points={`${pad},${height} ${points.join(" ")} ${width - pad},${height}`}
        fill="var(--accent-soft)" stroke="none" />
      <polyline points={points.join(" ")} fill="none" stroke="var(--accent)" strokeWidth="1.6"
        strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
      <circle cx={x(last)} cy={y(values[last])} r="3" fill="var(--accent)" />
    </svg>
  );
}

// ---------- time helpers ----------
export function ago(iso: string): string {
  const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
export const full = (iso: string) => new Date(iso).toLocaleString();
