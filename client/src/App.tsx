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
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API}/session`, { method: "POST" })
      .then((r) => r.json())
      .then((data) => setSessionId(data.session_id));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim() || !sessionId || streaming) return;

    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "human", content: text }]);
    setStreaming(true);
    setMessages((prev) => [...prev, { role: "ai", content: "" }]);

    const response = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, text }),
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      for (const line of decoder.decode(value).split("\n")) {
        if (!line.startsWith("data: ")) continue;
        const event = JSON.parse(line.slice(6));
        if (event.event === "token") {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "ai",
              content: next[next.length - 1].content + event.delta,
            };
            return next;
          });
        }
      }
    }

    setStreaming(false);
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
        <div ref={bottomRef} />
      </div>
      <div className="input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={sessionId ? "Type a message..." : "Connecting..."}
          disabled={!sessionId || streaming}
          rows={2}
        />
        <button onClick={sendMessage} disabled={!sessionId || streaming || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
