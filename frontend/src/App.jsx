import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import AssessmentPage from './pages/AssessmentPage'
import LessonPage from './pages/LessonPage'
import PracticePage from './pages/PracticePage'
import ProfilePage from './pages/ProfilePage'
import LevelUpPage from './pages/LevelUpPage'

function RequireAuth({ children }) {
  const raw = localStorage.getItem('vocai_user')
  if (!raw) return <Navigate to="/" replace />
  return children
}

function RequireLevel({ children }) {
  const raw = localStorage.getItem('vocai_user')
  if (!raw) return <Navigate to="/" replace />
  const user = JSON.parse(raw)
  // Seviye belirlenmemişse assessment'a yönlendir
  if (!user.cefr_level || user.cefr_level === '') {
    return <Navigate to="/assessment" replace />
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/assessment" element={<RequireAuth><AssessmentPage /></RequireAuth>} />
        <Route path="/lesson" element={<RequireLevel><LessonPage /></RequireLevel>} />
        <Route path="/practice/:sessionId" element={<RequireLevel><PracticePage /></RequireLevel>} />
        <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
        <Route path="/levelup" element={<RequireLevel><LevelUpPage /></RequireLevel>} />
      </Routes>
    </BrowserRouter>
  )
}
