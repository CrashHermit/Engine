import type { World, CreateWorldPayload } from '../types'

const MOCK_WORLDS: World[] = [
  {
    id: '1',
    name: 'The Shattered Realm',
    description: 'A land torn apart by an ancient cataclysm, where the remnants of old kingdoms struggle to survive.',
    created_at: '2026-01-15T10:00:00Z',
  },
]

export async function getWorlds(): Promise<World[]> {
  return Promise.resolve([...MOCK_WORLDS])
}

export async function createWorld(payload: CreateWorldPayload): Promise<World> {
  const world: World = {
    id: String(Date.now()),
    name: payload.name,
    description: payload.description,
    created_at: new Date().toISOString(),
  }
  MOCK_WORLDS.push(world)
  return Promise.resolve({ ...world })
}

export async function deleteWorld(worldId: string): Promise<void> {
  const idx = MOCK_WORLDS.findIndex(w => w.id === worldId)
  if (idx !== -1) MOCK_WORLDS.splice(idx, 1)
}
