import type { Character, CreateCharacterPayload } from '../types'

// Stub data until backend endpoints are wired up
const MOCK_CHARACTERS: Character[] = [
  {
    id: '1',
    name: 'Aldric the Grey',
    description: 'A weathered wanderer who has walked the forgotten roads between kingdoms, carrying secrets older than the stones beneath his boots.',
    corpus_score: 2,
    mens_score: 2,
    anima_score: 1,
    extraversion_score: 2,
    openness_score: 3,
    agreeableness_score: 4,
    neuroticism_score: 2,
    conscientiousness_score: 3,
  },
  {
    id: '2',
    name: 'Seraphine Voss',
    description: 'Once a scribe in a fallen monastery, she now seeks the lost texts that could rewrite the laws of the mortal world.',
    corpus_score: 1,
    mens_score: 4,
    anima_score: 0,
    extraversion_score: 1,
    openness_score: 5,
    agreeableness_score: 3,
    neuroticism_score: 4,
    conscientiousness_score: 5,
  },
]

export async function getCharacters(): Promise<Character[]> {
  // TODO: replace with real API call
  // const res = await fetch('/characters')
  // return res.json()
  return Promise.resolve([...MOCK_CHARACTERS])
}

export async function createCharacter(payload: CreateCharacterPayload): Promise<Character> {
  // TODO: replace with real API call
  // const res = await fetch('/characters', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  // return res.json()
  const newChar: Character = { id: String(Date.now()), ...payload }
  MOCK_CHARACTERS.push(newChar)
  return Promise.resolve(newChar)
}

export async function deleteCharacter(characterId: string): Promise<void> {
  // TODO: replace with real API call
  // await fetch(`/characters/${characterId}`, { method: 'DELETE' })
  const idx = MOCK_CHARACTERS.findIndex(c => c.id === characterId)
  if (idx !== -1) MOCK_CHARACTERS.splice(idx, 1)
}

export async function startSession(characterId: string): Promise<void> {
  // TODO: replace with real API call
  // await fetch('/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ character_id: characterId }) })
  console.log('Session started for character:', characterId)
}
