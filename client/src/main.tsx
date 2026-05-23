import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import StartScreen from './screens/StartScreen'
import SavesListScreen from './screens/SavesListScreen'
import CreateWorldScreen from './screens/CreateWorldScreen'
import WorldDetailScreen from './screens/WorldDetailScreen'
import CreateCharacterScreen from './screens/CreateCharacterScreen'
import GameScreen from './screens/GameScreen'

const router = createBrowserRouter([
  { path: '/', element: <StartScreen /> },
  { path: '/worlds', element: <SavesListScreen /> },
  { path: '/worlds/create', element: <CreateWorldScreen /> },
  { path: '/worlds/:worldId', element: <WorldDetailScreen /> },
  { path: '/worlds/:worldId/characters/create', element: <CreateCharacterScreen /> },
  { path: '/game', element: <GameScreen /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
