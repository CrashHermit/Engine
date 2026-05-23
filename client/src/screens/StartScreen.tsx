import { useNavigate } from 'react-router-dom'

export default function StartScreen() {
  const navigate = useNavigate()

  return (
    <div className="screen start-screen">
      <div className="start-content">
        <h1 className="game-title">Dark Adventures</h1>
        <p className="game-subtitle">A tale written in shadow and steel</p>
        <div className="hub-actions">
          <button className="hub-card" onClick={() => navigate('/worlds')}>
            <span className="hub-card__icon">⚔</span>
            <span className="hub-card__label">Load World</span>
            <span className="hub-card__desc">Return to a world you have already shaped.</span>
          </button>
          <button className="hub-card" onClick={() => navigate('/worlds/create')}>
            <span className="hub-card__icon">✦</span>
            <span className="hub-card__label">New World</span>
            <span className="hub-card__desc">Forge a new world and begin your legend.</span>
          </button>
        </div>
      </div>
    </div>
  )
}
