import { useEffect, useMemo, useRef, useState } from "react";

export interface PaletteItem { label: string; hint: string; run: () => void }

// Ctrl+K: type a few letters, press Enter.
export default function Palette({ items, onClose }: { items: PaletteItem[]; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => input.current?.focus(), []);

  const shown = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    return items.filter((item) => words.every((word) => item.label.toLowerCase().includes(word)));
  }, [items, query]);

  const choose = (item: PaletteItem | undefined) => { if (item) { onClose(); item.run(); } };

  return (
    <div className="palette-back" onMouseDown={onClose}>
      <div className="palette" role="dialog" aria-label="Command palette" onMouseDown={(e) => e.stopPropagation()}>
        <input
          id="palette-input" ref={input} value={query} placeholder="Type a page or action"
          onChange={(e) => { setQuery(e.target.value); setSelected(0); }}
          onKeyDown={(e) => {
            if (e.key === "Escape") onClose();
            else if (e.key === "ArrowDown") { e.preventDefault(); setSelected((i) => Math.min(i + 1, shown.length - 1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setSelected((i) => Math.max(i - 1, 0)); }
            else if (e.key === "Enter") choose(shown[selected]);
          }}
        />
        {shown.length === 0 ? (
          <div className="none">Nothing matches "{query}".</div>
        ) : (
          <ul>
            {shown.map((item, index) => (
              <li key={item.label}>
                <button aria-selected={index === selected} onMouseEnter={() => setSelected(index)} onClick={() => choose(item)}>
                  <span>{item.label}</span>
                  <span className="muted">{item.hint}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
