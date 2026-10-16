import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { api, ChatStep, ChatTurn, messageOf } from "../api";
import { ErrorBanner, Icon } from "../ui";

interface Message extends ChatTurn {
  steps?: ChatStep[];
}

const EXAMPLES = [
  "What orders came in today?",
  "List the products in the store.",
  "Convert 100 USD to INR.",
  "Convert the total of my latest order to INR.",
];

// One tool call, shown so you can see exactly what the assistant did.
function Step({ step }: { step: ChatStep }) {
  return (
    <details className={"step" + (step.failed ? " failed" : "")}>
      <summary>
        <code>{step.tool}</code>
        <span className="muted">{step.duration_ms} ms</span>
        <span className={"pill " + (step.failed ? "gateway_error" : "success")}>{step.failed ? "Failed" : "Done"}</span>
      </summary>
      <div className="step-body">
        <div className="muted">Arguments</div>
        <pre>{JSON.stringify(step.arguments, null, 2)}</pre>
        <div className="muted">Result</div>
        <pre>{step.result}</pre>
      </div>
    </details>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [messages, busy]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy) return;
    const next: Message[] = [...messages, { role: "user", content: question }];
    setMessages(next);
    setDraft("");
    setError("");
    setBusy(true);
    try {
      // Only the words are sent back. The tool call details stay in the browser.
      const answer = await api.chat(next.map(({ role, content }) => ({ role, content })));
      setMessages([...next, { role: "assistant", content: answer.reply, steps: answer.steps }]);
    } catch (problem) {
      setError(messageOf(problem));
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    send(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send(draft);
    }
  }

  return (
    <div className="chat">
      <div className="page-head">
        <div>
          <h1>Chat</h1>
          <p>Ask a question. The assistant uses the same tools you can use, as you, and shows every tool it called.</p>
        </div>
        {messages.length > 0 && <button className="btn" onClick={() => { setMessages([]); setError(""); }}>New chat</button>}
      </div>

      <div className="transcript" aria-live="polite">
        {messages.length === 0 && (
          <div className="chat-empty">
            <h3>Try a question</h3>
            <div className="chips">
              {EXAMPLES.map((example) => (
                <button key={example} className="chip" onClick={() => send(example)}>{example}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={"bubble " + message.role}>
            {message.steps && message.steps.length > 0 && (
              <div className="steps">
                <div className="muted">Tools called</div>
                {message.steps.map((step, i) => <Step key={i} step={step} />)}
              </div>
            )}
            <div className="bubble-text">{message.content || "(no answer)"}</div>
          </div>
        ))}

        {busy && <div className="bubble assistant muted">Thinking…</div>}
        <div ref={end} />
      </div>

      {error && <ErrorBanner text={error} />}

      <form className="composer" onSubmit={onSubmit}>
        <label htmlFor="chat-draft" className="visually-hidden">Your message</label>
        <textarea id="chat-draft" className="input" rows={2} value={draft} placeholder="Ask about products, orders or exchange rates…"
          onChange={(e) => setDraft(e.target.value)} onKeyDown={onKeyDown} />
        <button className="btn primary" disabled={busy || !draft.trim()}><Icon name="chat" size={16} /> Send</button>
      </form>
    </div>
  );
}
