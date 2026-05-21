import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const LEVEL_COLORS = {
  A1: 'bg-green-100 text-green-700',
  A2: 'bg-green-100 text-green-700',
  B1: 'bg-blue-100 text-blue-700',
  B2: 'bg-blue-100 text-blue-700',
  C1: 'bg-purple-100 text-purple-700',
  C2: 'bg-purple-100 text-purple-700',
}

const EXERCISE_TYPE_LABELS = {
  fill_in_blank: 'Fill in the Blank',
  multiple_choice: 'Multiple Choice',
  writing_prompt: 'Writing',
}

function SkillCard({ skill }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-700 capitalize">{skill.name}</span>
        <span className="text-xs text-gray-400">{skill.duration_minutes} min</span>
      </div>
      <p className="text-xs text-gray-500">{skill.focus}</p>
    </div>
  )
}

function ExerciseCard({ exercise, index }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="bg-brand-50 text-brand-600 text-xs font-semibold px-2 py-1 rounded-lg shrink-0">
          {index + 1}
        </span>
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">
            {EXERCISE_TYPE_LABELS[exercise.type] || exercise.type}
          </p>
          <p className="text-sm text-gray-800 font-medium">{exercise.instruction}</p>
          {exercise.content && (
            <p className="text-sm text-gray-600 mt-2 italic">{exercise.content}</p>
          )}
          {exercise.options && (
            <ul className="mt-2 space-y-1">
              {exercise.options.map((opt, i) => (
                <li key={i} className="text-sm text-gray-600">{opt}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

export default function LessonPage() {
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const user = JSON.parse(localStorage.getItem('vocai_user'))

  useEffect(() => {
    api.getTodayLesson(user.user_id)
      .then((data) => {
        setLesson(data)
        localStorage.setItem('vocai_current_lesson', JSON.stringify(data))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  function handleLogout() {
    localStorage.removeItem('vocai_user')
    localStorage.removeItem('vocai_current_lesson')
    navigate('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 gap-3">
        <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Preparing your lesson...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    )
  }

  const curriculum = lesson?.curriculum || {}
  const content = lesson?.content || {}
  const skills = curriculum.skills || []
  const exercises = content.exercises || []
  const readingText = content.reading_text
  const grammarNote = content.grammar_note
  const vocabularyList = content.vocabulary_list || []

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-brand-600">VocAI</h1>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-semibold px-2 py-1 rounded-lg ${LEVEL_COLORS[user.cefr_level] || 'bg-gray-100 text-gray-600'}`}>
            {user.cefr_level}
          </span>
          <button
            onClick={() => navigate('/profile')}
            className="text-sm text-gray-600 hover:text-brand-600 font-medium px-2 py-1 rounded-lg hover:bg-brand-50 transition"
          >
            {user.username}
          </button>
          <button onClick={handleLogout} className="text-xs text-gray-400 hover:text-gray-600">
            Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Title & Objectives */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900">{curriculum.title || 'Daily Lesson'}</h2>
          {curriculum.learning_objectives && (
            <ul className="mt-2 space-y-1">
              {curriculum.learning_objectives.map((obj, i) => (
                <li key={i} className="text-sm text-gray-500 flex items-start gap-2">
                  <span className="text-brand-500 mt-0.5">•</span> {obj}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Skills */}
        {skills.length > 0 && (
          <section className="mb-8">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Skills</h3>
            <div className="grid grid-cols-2 gap-3">
              {skills.map((skill, i) => <SkillCard key={i} skill={skill} />)}
            </div>
          </section>
        )}

        {/* Grammar Note */}
        {grammarNote && (
          <section className="mb-8">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Grammar Note</h3>
            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
              <p className="text-sm text-amber-900 leading-relaxed">{grammarNote}</p>
            </div>
          </section>
        )}

        {/* Reading Text */}
        {readingText && (
          <section className="mb-8">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Reading</h3>
            <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
              <p className="text-sm text-gray-700 leading-relaxed">{readingText}</p>
            </div>
          </section>
        )}

        {/* Vocabulary */}
        {vocabularyList.length > 0 && (
          <section className="mb-8">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
              Vocabulary ({vocabularyList.length})
            </h3>
            <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
              <div className="grid grid-cols-1 gap-2">
                {vocabularyList.map((item, i) => {
                  const [word, ...rest] = item.split(':')
                  return (
                    <div key={i} className="flex gap-2 text-sm">
                      <span className="font-medium text-brand-700 min-w-[130px]">{word.trim()}</span>
                      <span className="text-gray-500">{rest.join(':').trim()}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </section>
        )}

        {/* Exercises preview */}
        {exercises.length > 0 && (
          <section className="mb-8">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
              Exercises ({exercises.length})
            </h3>
            <div className="space-y-3">
              {exercises.map((ex, i) => <ExerciseCard key={i} exercise={ex} index={i} />)}
            </div>
          </section>
        )}

        <button
          onClick={() => navigate(`/practice/${lesson.session_id}`)}
          className="w-full bg-brand-600 text-white rounded-xl py-3 text-sm font-medium hover:bg-brand-700 transition"
        >
          Start Practice →
        </button>
      </main>
    </div>
  )
}
