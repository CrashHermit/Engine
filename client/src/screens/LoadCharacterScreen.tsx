import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import PipSelector from '../components/PipSelector'
import { getCharacters, startSession } from '../api/characters'
import type { Character } from '../types'

export default function LoadCharacterScreen() {
  const navigate = useNavigate()
  const [characters, setCharacters] = useState<Character[]>([])
  const [selected, setSelected] = useState<Character | null>(null)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    getCharacters().then(chars => {
      setCharacters(chars)
      if (chars.length > 0) setSelected(chars[0])
      setLoading(false)
    })
  }, [])

  async function handlePlay() {
    if (!selected) return
    setStarting(true)
    await startSession(selected.id)
    navigate('/game')
  }

  return (
    <div className="screen load-screen">
      <div className="load-layout">
        <aside className="char-list">
          <h2 className="char-list__title">Characters</h2>
          {loading && <p className="char-list__empty">Loading…</p>}
          {!loading && characters.length === 0 && (
            <p className="char-list__empty">No characters yet.</p>
          )}
          {characters.map(c => (
            <button
              key={c.id}
              className={`char-list__item ${selected?.id === c.id ? 'char-list__item--active' : ''}`}
              onClick={() => setSelected(c)}
            >
              {c.name}
            </button>
          ))}
          <button className="btn btn--ghost char-list__new" onClick={() => navigate('/characters/create')}>
            + New Character
          </button>
        </aside>

        <div className="char-detail">
          {selected ? (
            <>
              <div className="char-detail__body">
                <h2 className="char-detail__name">{selected.name}</h2>
                <p className="char-detail__desc">{selected.description || <em>No description.</em>}</p>
                <div className="char-detail__attrs">
                  <PipSelector label="Corpus" value={selected.corpus_score} readonly />
                  <PipSelector label="Mens" value={selected.mens_score} readonly />
                  <PipSelector label="Anima" value={selected.anima_score} readonly />
                </div>
              </div>
            </>
          ) : (
            <div className="char-detail__empty">
              <p>Select a character to begin.</p>
            </div>
          )}
        </div>
      </div>

      <div className="load-footer">
        <button className="btn btn--ghost" onClick={() => navigate('/characters')}>
          Back
        </button>
        <button
          className="btn btn--primary btn--large"
          disabled={!selected || starting}
          onClick={handlePlay}
        >
          {starting ? 'Entering…' : 'Play'}
        </button>
      </div>
    </div>
  )
}
