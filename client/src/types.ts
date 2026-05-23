export interface Character {
  id: string
  name: string
  description: string
  corpus_score: number
  mens_score: number
  anima_score: number
}

export interface CreateCharacterPayload {
  name: string
  description: string
  corpus_score: number
  mens_score: number
  anima_score: number
}
