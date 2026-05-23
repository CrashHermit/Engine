import { useState, useRef, useEffect } from 'react'
import type { Message } from '../api/chat'

interface ChatPanelProps {
  title: string
  messages: Message[]
  loading: boolean
  onSend: (text: string) => void
  aiLabel?: string
  placeholder?: string
}

export default function ChatPanel({ title, messages, loading, onSend, aiLabel = 'Narrator', placeholder = 'Speak…' }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
    if (isNearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  function handleSend() {
    const text = input.trim()
    if (!text) return
    setInput('')
    onSend(text)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-panel__header">
        <span className="chat-panel__title">{title}</span>
      </div>
      <div className="chat-panel__messages" ref={containerRef}>
        {messages.map(msg => (
          <div key={msg.id} className={`chat-msg chat-msg--${msg.role}`}>
            <span className="chat-msg__label">{msg.role === 'human' ? 'You' : aiLabel}</span>
            <p className="chat-msg__text">{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div className="chat-msg chat-msg--ai">
            <span className="chat-msg__label">{aiLabel}</span>
            <p className="chat-msg__text chat-msg__text--loading">
              <span />
              <span />
              <span />
            </p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-panel__input-area">
        <textarea
          className="chat-panel__input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-label={title}
          rows={2}
        />
        <button className="btn btn--primary chat-panel__send" onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  )
}
