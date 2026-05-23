import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import ChatPanel from '../components/ChatPanel'
import { sendMessage, sendOocMessage, makeMessage } from '../api/chat'
import type { Message } from '../api/chat'

export default function GameScreen() {
  const navigate = useNavigate()
  const location = useLocation()
  const worldId = (location.state as { worldId?: string })?.worldId
  const [icMessages, setIcMessages] = useState<Message[]>([])
  const [oocMessages, setOocMessages] = useState<Message[]>([])
  const [icLoading, setIcLoading] = useState(false)
  const [oocLoading, setOocLoading] = useState(false)
  const [icError, setIcError] = useState('')
  const [oocError, setOocError] = useState('')

  async function handleIcSend(text: string) {
    setIcError('')
    setIcMessages(prev => [...prev, makeMessage('human', text)])
    setIcLoading(true)
    try {
      const reply = await sendMessage(text)
      setIcMessages(prev => [...prev, makeMessage('ai', reply)])
    } catch {
      setIcError('The narrator did not respond. Try again.')
    } finally {
      setIcLoading(false)
    }
  }

  async function handleOocSend(text: string) {
    setOocError('')
    setOocMessages(prev => [...prev, makeMessage('human', text)])
    setOocLoading(true)
    try {
      const reply = await sendOocMessage(text)
      setOocMessages(prev => [...prev, makeMessage('ai', reply)])
    } catch {
      setOocError('The GM did not respond. Try again.')
    } finally {
      setOocLoading(false)
    }
  }

  return (
    <div className="screen game-screen">
      <header className="game-header">
        <span className="game-header__title">Dark Adventures</span>
        <button className="btn btn--ghost game-header__menu" onClick={() => navigate(worldId ? `/worlds/${worldId}` : '/worlds')}>
          ← World
        </button>
      </header>

      <div className="game-body">
        <aside className="scene-panel">
          <span className="scene-panel__label">Scene</span>
        </aside>

        <div className="chat-panel-wrapper">
          {icError && <p className="chat-error">{icError}</p>}
          <ChatPanel
            title="In Character"
            messages={icMessages}
            loading={icLoading}
            onSend={handleIcSend}
            aiLabel="Narrator"
            placeholder="What do you do?"
          />
        </div>

        <div className="chat-panel-wrapper">
          {oocError && <p className="chat-error">{oocError}</p>}
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
    </div>
  )
}
