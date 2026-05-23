import { useNavigate } from 'react-router-dom'

export default function CharacterHubScreen() {
  const navigate = useNavigate()

  return (
    <div className="screen hub-screen">
      <div className="hub-content">
        <h2 className="hub-title">Choose Your Path</h2>
        <div className="hub-actions">
          <button className="hub-card" onClick={() => navigate('/characters/create')}>
            <span className="hub-card__icon">✦</span>
            <span className="hub-card__label">Create Character</span>
            <span className="hub-card__desc">Forge a new soul for the journey ahead</span>
          </button>
          <button className="hub-card" onClick={() => navigate('/characters/load')}>
            <span className="hub-card__icon">⟐</span>
            <span className="hub-card__label">Load Character</span>
            <span className="hub-card__desc">Return to a hero already written</span>
          </button>
        </div>
      </div>
    </div>
  )
}
