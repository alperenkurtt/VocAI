import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const LEVEL_COLORS = {
  A1: 'bg-green-100 text-green-700 border-green-200',
  A2: 'bg-green-100 text-green-700 border-green-200',
  B1: 'bg-blue-100 text-blue-700 border-blue-200',
  B2: 'bg-blue-100 text-blue-700 border-blue-200',
  C1: 'bg-purple-100 text-purple-700 border-purple-200',
  C2: 'bg-purple-100 text-purple-700 border-purple-200',
}

const SKILL_ICONS = { grammar: '📐', vocabulary: '📚', reading: '👁️', writing: '✍️' }

function scoreColor(score) {
  if (score >= 85) return 'bg-green-500'
  if (score >= 70) return 'bg-blue-500'
  if (score >= 50) return 'bg-amber-400'
  return 'bg-red-400'
}

function SkillBar({ skillKey, score }) {
  return (
    <div className="mb-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700 capitalize">
          {SKILL_ICONS[skillKey]} {skillKey.charAt(0).toUpperCase() + skillKey.slice(1)}
        </span>
        <span className="text-sm font-bold text-gray-800">
          {score}<span className="text-xs text-gray-400 font-normal">/100</span>
        </span>
      </div>
      <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${scoreColor(score)}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}

const LEVEL_UP_THRESHOLDS = {
  A1: { min_sessions: 8,  avg_score_pct: 72, recent: 5,  skill_min: 45 },
  A2: { min_sessions: 10, avg_score_pct: 74, recent: 6,  skill_min: 55 },
  B1: { min_sessions: 12, avg_score_pct: 76, recent: 7,  skill_min: 65 },
  B2: { min_sessions: 15, avg_score_pct: 78, recent: 8,  skill_min: 75 },
  C1: { min_sessions: 18, avg_score_pct: 81, recent: 10, skill_min: 85 },
}

function LevelProgress({ profile }) {
  const level = profile.cefr_level || 'A1'
  const req = LEVEL_UP_THRESHOLDS[level] || LEVEL_UP_THRESHOLDS.A1
  const sessions = profile.sessions_at_current_level ?? profile.total_sessions ?? 0
  const skills = profile.skill_scores || {}
  const weakSkills = Object.entries(skills).filter(([, v]) => v < req.skill_min)
  const sessionsOk = sessions >= req.min_sessions
  const skillsOk = weakSkills.length === 0

  const Tick = ({ ok }) => (
    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0 ${ok ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
      {ok ? '✓' : '○'}
    </span>
  )

  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
      <h3 className="font-semibold text-gray-900 mb-4">Level Up Requirements</h3>
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <Tick ok={sessionsOk} />
          <span className="text-sm text-gray-700">
            At least {req.min_sessions} practice sessions
            <span className={`ml-2 font-semibold ${sessionsOk ? 'text-green-600' : 'text-gray-400'}`}>
              ({sessions}/{req.min_sessions})
            </span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Tick ok={false} />
          <span className="text-sm text-gray-700">
            {req.avg_score_pct}%+ average on last {req.recent} sessions
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Tick ok={skillsOk} />
          <span className="text-sm text-gray-700">
            All skills above {req.skill_min}
            {weakSkills.length > 0 && (
              <span className="ml-2 text-amber-600 text-xs">
                (Needs improvement: {weakSkills.map(([k]) => k).join(', ')})
              </span>
            )}
          </span>
        </div>
      </div>
      <p className="text-xs text-gray-400 mt-4 leading-relaxed">
        When all conditions are met, you'll see a level-up suggestion at the end of a practice session.
      </p>
    </div>
  )
}

export default function ProfilePage() {
  const navigate = useNavigate()
  const localUser = JSON.parse(localStorage.getItem('vocai_user'))
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getUser(localUser.user_id)
      .then(setProfile)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  function handleReassess() {
    const updated = { ...localUser, cefr_level: '' }
    localStorage.setItem('vocai_user', JSON.stringify(updated))
    localStorage.removeItem('vocai_current_lesson')
    navigate('/assessment')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="w-7 h-7 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-red-500 text-sm">{error || 'Could not load profile'}</p>
      </div>
    )
  }

  const skills = profile.skill_scores || {}
  const level = profile.cefr_level || '—'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <button onClick={() => navigate('/lesson')} className="text-sm text-gray-400 hover:text-gray-600">
          ← Back to Lesson
        </button>
        <h1 className="text-lg font-semibold text-brand-600">Profile</h1>
        <span className="w-24" />
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-5">
        {/* User card */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex items-center gap-5">
          <div className="w-14 h-14 rounded-full bg-brand-100 flex items-center justify-center text-2xl font-bold text-brand-600">
            {profile.username?.[0]?.toUpperCase()}
          </div>
          <div className="flex-1">
            <p className="font-semibold text-gray-900 text-lg">{profile.username}</p>
            <p className="text-sm text-gray-400">{profile.total_sessions} sessions completed</p>
          </div>
          <span className={`text-sm font-bold px-3 py-1.5 rounded-xl border ${LEVEL_COLORS[level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
            {level}
          </span>
        </div>

        {/* Skill scores */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-5">Skill Scores</h3>
          {Object.entries(skills).map(([key, val]) => (
            <SkillBar key={key} skillKey={key} score={val} />
          ))}
          <p className="text-xs text-gray-400 mt-1">Scores update gradually after each practice session.</p>
        </div>

        {/* Level up requirements */}
        {level && level !== '—' && level !== 'C2' && (
          <LevelProgress profile={profile} />
        )}

        {/* Re-assessment */}
        <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-1">Level Assessment</h3>
          <p className="text-sm text-gray-500 mb-4">
            If you think your current level isn't accurate, you can retake the placement test.
            This will reset your current level and start a new assessment.
          </p>
          <button
            onClick={handleReassess}
            className="w-full border border-brand-600 text-brand-600 rounded-xl py-2.5 text-sm font-medium hover:bg-brand-50 transition"
          >
            Retake Level Assessment
          </button>
        </div>
      </main>
    </div>
  )
}
