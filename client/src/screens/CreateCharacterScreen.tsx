import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PipSelector from '../components/PipSelector'
import { createCharacter } from '../api/characters'

const POOL = 5
const MAX_PER_ATTR = 4

export default function CreateCharacterScreen() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [corpus, setCorpus] = useState(0)
  const [mens, setMens] = useState(0)
  const [anima, setAnima] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const spent = corpus + mens + anima
  const remaining = POOL - spent

  function clampSet(setter: (v: number) => void, current: number) {
    return (next: number) => {
      const delta = next - current
      if (delta > 0 && remaining - delta < 0) return
      if (next > MAX_PER_ATTR) return
      setter(next)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError('Your character needs a name.'); return }
    if (spent !== POOL) { setError(`Distribute all ${POOL} points before continuing.`); return }
    setError('')
    setSubmitting(true)
    try {
      await createCharacter({ name: name.trim(), description: description.trim(), corpus_score: corpus, mens_score: mens, anima_score: anima })
      navigate('/characters/load')
    } catch {
      setError('Something went wrong. Try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="screen create-screen">
      <form className="create-form" onSubmit={handleSubmit}>
        <h2 className="form-title">Forge Your Character</h2>

        <div className="form-field">
          <label className="form-label" htmlFor="char-name">Name</label>
          <input
            id="char-name"
            className="form-input"
            type="text"
            placeholder="What are you called?"
            value={name}
            onChange={e => setName(e.target.value)}
            maxLength={60}
          />
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="char-desc">Description</label>
          <textarea
            id="char-desc"
            className="form-textarea"
            placeholder="Who are you, and what brought you here?"
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={4}
          />
        </div>

        <div className="form-attributes">
          <div className="attr-header">
            <span className="attr-title">Attributes</span>
            <span className={`attr-pool ${remaining === 0 ? 'attr-pool--spent' : ''}`}>
              {remaining} point{remaining !== 1 ? 's' : ''} remaining
            </span>
          </div>
          <PipSelector label="Corpus" value={corpus} onChange={clampSet(setCorpus, corpus)} />
          <PipSelector label="Mens" value={mens} onChange={clampSet(setMens, mens)} />
          <PipSelector label="Anima" value={anima} onChange={clampSet(setAnima, anima)} />
        </div>

        {error && <p className="form-error">{error}</p>}

        <div className="form-actions">
          <button type="button" className="btn btn--ghost" onClick={() => navigate('/characters')}>
            Back
          </button>
          <button type="submit" className="btn btn--primary" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  )
}
