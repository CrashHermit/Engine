import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import StartScreen from './screens/StartScreen'
import CharacterHubScreen from './screens/CharacterHubScreen'
import CreateCharacterScreen from './screens/CreateCharacterScreen'
import LoadCharacterScreen from './screens/LoadCharacterScreen'

const router = createBrowserRouter([
  { path: '/', element: <StartScreen /> },
  { path: '/characters', element: <CharacterHubScreen /> },
  { path: '/characters/create', element: <CreateCharacterScreen /> },
  { path: '/characters/load', element: <LoadCharacterScreen /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
