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
  const [extraversion, setExtraversion] = useState(0)
  const [openness, setOpenness] = useState(0)
  const [agreeableness, setAgreeableness] = useState(0)
  const [neuroticism, setNeuroticism] = useState(0)
  const [conscientiousness, setConscientiousness] = useState(0)
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
    if ([extraversion, openness, agreeableness, neuroticism, conscientiousness].some(v => v === 0)) {
      setError('Rate all five personality traits before continuing.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      await createCharacter({
        name: name.trim(),
        description: description.trim(),
        corpus_score: corpus,
        mens_score: mens,
        anima_score: anima,
        extraversion_score: extraversion,
        openness_score: openness,
        agreeableness_score: agreeableness,
        neuroticism_score: neuroticism,
        conscientiousness_score: conscientiousness,
      })
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

        <div className="form-attributes">
          <div className="attr-header">
            <span className="attr-title">Personality</span>
          </div>
          <PipSelector label="Extraversion" value={extraversion} max={5} onChange={setExtraversion} />
          <PipSelector label="Openness" value={openness} max={5} onChange={setOpenness} />
          <PipSelector label="Agreeableness" value={agreeableness} max={5} onChange={setAgreeableness} />
          <PipSelector label="Neuroticism" value={neuroticism} max={5} onChange={setNeuroticism} />
          <PipSelector label="Conscientiousness" value={conscientiousness} max={5} onChange={setConscientiousness} />
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
