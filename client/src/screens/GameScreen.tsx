import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ChatPanel from '../components/ChatPanel'
import { sendMessage, sendOocMessage } from '../api/chat'
import type { Message } from '../api/chat'

export default function GameScreen() {
  const navigate = useNavigate()
  const [icMessages, setIcMessages] = useState<Message[]>([])
  const [oocMessages, setOocMessages] = useState<Message[]>([])
  const [icLoading, setIcLoading] = useState(false)
  const [oocLoading, setOocLoading] = useState(false)

  async function handleIcSend(text: string) {
    setIcMessages(prev => [...prev, { role: 'human', content: text }])
    setIcLoading(true)
    try {
      const reply = await sendMessage(text)
      setIcMessages(prev => [...prev, { role: 'ai', content: reply }])
    } finally {
      setIcLoading(false)
    }
  }

  async function handleOocSend(text: string) {
    setOocMessages(prev => [...prev, { role: 'human', content: text }])
    setOocLoading(true)
    try {
      const reply = await sendOocMessage(text)
      setOocMessages(prev => [...prev, { role: 'ai', content: reply }])
    } finally {
      setOocLoading(false)
    }
  }

  return (
    <div className="screen game-screen">
      <header className="game-header">
        <span className="game-header__title">Dark Adventures</span>
        <button className="btn btn--ghost game-header__menu" onClick={() => navigate('/')}>
          ← Main Menu
        </button>
      </header>

      <div className="game-body">
        <aside className="scene-panel">
          <span className="scene-panel__label">Scene</span>
        </aside>

        <ChatPanel
          title="In Character"
          messages={icMessages}
          loading={icLoading}
          onSend={handleIcSend}
          aiLabel="Narrator"
          placeholder="What do you do?"
        />

        <ChatPanel
          title="Out of Character"
          messages={oocMessages}
          loading={oocLoading}
          onSend={handleOocSend}
          aiLabel="GM"
          placeholder="Ask the GM…"
        />
      </div>
    </div>
  )
}
