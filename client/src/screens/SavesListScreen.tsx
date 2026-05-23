import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getWorlds, deleteWorld } from '../api/worlds'
import { getAllCharacters } from '../api/characters'
import type { World } from '../types'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function SavesListScreen() {
  const navigate = useNavigate()
  const [worlds, setWorlds] = useState<World[]>([])
  const [characterCounts, setCharacterCounts] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    Promise.all([getWorlds(), getAllCharacters()]).then(([ws, chars]) => {
      setWorlds(ws)
      const counts: Record<string, number> = {}
      chars.forEach(c => { counts[c.world_id] = (counts[c.world_id] || 0) + 1 })
      setCharacterCounts(counts)
      setLoading(false)
    })
  }, [])

  async function handleDelete(worldId: string) {
    setDeleting(true)
    try {
      await deleteWorld(worldId)
      setWorlds(prev => prev.filter(w => w.id !== worldId))
      setConfirmDelete(null)
    } catch (error) {
      console.error('Failed to delete world:', error)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="screen saves-screen">
      <div className="saves-header">
        <h2 className="saves-header__title">Your Worlds</h2>
      </div>

      <div className="saves-body">
        {loading && <p className="saves-empty">Loading…</p>}
        {!loading && worlds.length === 0 && (
          <p className="saves-empty">No worlds yet. Create one to begin.</p>
        )}
        {worlds.map(world => {
          const count = characterCounts[world.id] ?? 0
          return (
            <div key={world.id} className="saves-entry">
              {confirmDelete === world.id ? (
                <div className="saves-entry__confirm">
                  <p className="delete-confirm__text">
                    Delete <strong>{world.name}</strong> and all its characters? This cannot be undone.
                  </p>
                  <div className="delete-confirm__actions">
                    <button className="btn btn--ghost" onClick={() => setConfirmDelete(null)} disabled={deleting}>
                      Cancel
                    </button>
                    <button className="btn btn--danger" onClick={() => handleDelete(world.id)} disabled={deleting}>
                      {deleting ? 'Deleting…' : 'Delete'}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <button className="saves-entry__body" onClick={() => navigate(`/worlds/${world.id}`)}>
                    <span className="saves-entry__name">{world.name}</span>
                    <span className="saves-entry__meta">
                      {count} character{count !== 1 ? 's' : ''} · {formatDate(world.created_at)}
                    </span>
                  </button>
                  <button className="btn btn--ghost btn--delete" onClick={() => setConfirmDelete(world.id)}>
                    Delete
                  </button>
                </>
              )}
            </div>
          )
        })}
      </div>

      <div className="saves-footer">
        <button className="btn btn--ghost" onClick={() => navigate('/')}>
          ← Back
        </button>
        <button className="btn btn--primary" onClick={() => navigate('/worlds/create')}>
          + New World
        </button>
      </div>
    </div>
  )
}
