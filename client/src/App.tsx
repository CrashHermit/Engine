import { useEffect, useRef, useState } from "react";
import "./App.css";

const API = "";

interface Message {
  role: "human" | "ai";
  content: string;
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API}/session`, { method: "POST" })
      .then((r) => r.json())
      .then((data) => setSessionId(data.session_id));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    if (!input.trim() || !sessionId || loading) return;

    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "human", content: text }]);
    setLoading(true);

    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, text }),
      });

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "ai", content: data.content }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="app">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <span className="label">{msg.role === "human" ? "You" : "Narrator"}</span>
            <p>{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div className="message ai">
            <span className="label">Narrator</span>
            <p className="loading-dots">
              <span /><span /><span />
            </p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={sessionId ? "Type a message..." : "Connecting..."}
          disabled={!sessionId || loading}
          rows={2}
        />
        <button onClick={sendMessage} disabled={!sessionId || loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
