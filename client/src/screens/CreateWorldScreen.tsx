import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createWorld } from '../api/worlds'

export default function CreateWorldScreen() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError('Your world needs a name.'); return }
    setError('')
    setSubmitting(true)
    try {
      const world = await createWorld({ name: name.trim(), description: description.trim() })
      navigate(`/worlds/${world.id}`)
    } catch {
      setError('Something went wrong. Try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="screen create-screen">
      <form className="create-form" onSubmit={handleSubmit}>
        <h2 className="form-title">Shape a New World</h2>

        <div className="form-field">
          <label className="form-label" htmlFor="world-name">Name</label>
          <input
            id="world-name"
            className="form-input"
            type="text"
            placeholder="What is this world called?"
            value={name}
            onChange={e => setName(e.target.value)}
            maxLength={80}
          />
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="world-desc">Description</label>
          <textarea
            id="world-desc"
            className="form-textarea"
            placeholder="Describe this world…"
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={4}
          />
        </div>

        {error && <p className="form-error">{error}</p>}

        <div className="form-actions">
          <button type="button" className="btn btn--ghost" onClick={() => navigate('/')}>
            ← Back
          </button>
          <button type="submit" className="btn btn--primary" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create World'}
          </button>
        </div>
      </form>
    </div>
  )
}
