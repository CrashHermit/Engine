import { useNavigate } from 'react-router-dom'

export default function StartScreen() {
  const navigate = useNavigate()

  return (
    <div className="screen start-screen">
      <div className="start-content">
        <h1 className="game-title">Dark Adventures</h1>
        <p className="game-subtitle">A tale written in shadow and steel</p>
        <button className="btn btn--primary btn--large" onClick={() => navigate('/characters')}>
          Begin
        </button>
      </div>
    </div>
  )
}
