export interface Message {
  role: 'human' | 'ai'
  content: string
  id: string
}

export async function sendMessage(text: string): Promise<string> {
  const res = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error('Chat request failed')
  const data = await res.json()
  if (typeof data.content !== 'string') throw new Error('Invalid response format')
  return data.content
}

export async function sendOocMessage(text: string): Promise<string> {
  // TODO: wire to dedicated OOC/GM endpoint when available
  // const res = await fetch('/ooc', { method: 'POST', ... })
  console.log('OOC message sent:', text)
  return Promise.resolve('(The GM hears you…)')
}

export function makeMessage(role: Message['role'], content: string): Message {
  return { role, content, id: crypto.randomUUID() }
}
