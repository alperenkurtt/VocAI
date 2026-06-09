import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const TYPE_LABELS = {
  fill_in_blank: 'Fill in the Blank',
  multiple_choice: 'Multiple Choice',
  writing_prompt: 'Writing',
}

// Multiple choice — tıklanabilir seçenekler
function MultipleChoiceInput({ options = [], selected, onChange, submitted, correctAnswer }) {
  return (
    <div className="space-y-2 mt-3">
      {options.map((opt, i) => {
        const letter = opt.charAt(0) // "A", "B", ...
        const isSelected = selected === letter
        const isCorrect = correctAnswer && letter === correctAnswer

        let style = 'border-gray-200 bg-white text-gray-700 hover:border-brand-400 hover:bg-brand-50'
        if (submitted) {
          if (isCorrect) style = 'border-green-400 bg-green-50 text-green-800'
          else if (isSelected && !isCorrect) style = 'border-red-300 bg-red-50 text-red-700'
          else style = 'border-gray-100 bg-gray-50 text-gray-400'
        } else if (isSelected) {
          style = 'border-brand-500 bg-brand-50 text-brand-700'
        }

        return (
          <button
            key={i}
            onClick={() => !submitted && onChange(letter)}
            disabled={submitted}
            className={`w-full text-left px-4 py-2.5 rounded-xl border text-sm transition ${style}`}
          >
            {opt}
          </button>
        )
      })}
    </div>
  )
}

// Tek egzersiz bileşeni
function ExerciseCard({ exercise, index, answer, onChange, submitted }) {
  const isWriting = exercise.type === 'writing_prompt'

  return (
    <div className={`bg-white border rounded-xl p-5 shadow-sm transition ${
      submitted && exercise.type !== 'writing_prompt' && exercise.answer
        ? answer.trim().toLowerCase() === exercise.answer.trim().toLowerCase()
          ? 'border-green-300'
          : 'border-red-300'
        : 'border-gray-100'
    }`}>
      <div className="flex items-start gap-3 mb-3">
        <span className="bg-brand-50 text-brand-600 text-xs font-semibold px-2 py-1 rounded-lg shrink-0 mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">
            {TYPE_LABELS[exercise.type] || exercise.type}
          </p>
          <p className="text-sm text-gray-800 font-medium">{exercise.instruction}</p>
          {exercise.content && (
            <p className="text-sm text-gray-600 mt-2 italic leading-relaxed">{exercise.content}</p>
          )}
        </div>
      </div>

      {/* Multiple choice */}
      {exercise.type === 'multiple_choice' && (
        <MultipleChoiceInput
          options={exercise.options || []}
          selected={answer}
          onChange={(letter) => onChange(index, letter)}
          submitted={submitted}
          correctAnswer={exercise.answer}
        />
      )}

      {/* Fill in blank */}
      {exercise.type === 'fill_in_blank' && !submitted && (
        <input
          type="text"
          placeholder="Your answer..."
          value={answer}
          onChange={(e) => onChange(index, e.target.value)}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      )}

      {/* Writing prompt */}
      {exercise.type === 'writing_prompt' && !submitted && (
        <textarea
          rows={5}
          placeholder="Write 3–5 sentences..."
          value={answer}
          onChange={(e) => onChange(index, e.target.value)}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
        />
      )}

      {/* After submit: show answer for non-MC types */}
      {submitted && exercise.type !== 'multiple_choice' && (() => {
        const isWriting = exercise.type === 'writing_prompt'
        const isCorrect = !isWriting && exercise.answer &&
          answer.trim().toLowerCase() === exercise.answer.trim().toLowerCase()
        const isWrong = !isWriting && exercise.answer && !isCorrect

        return (
          <div className="space-y-2 mt-1">
            <div className={`rounded-lg px-3 py-2 border ${
              isWriting ? 'bg-gray-50 border-gray-200' :
              isCorrect ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300'
            }`}>
              <p className={`text-xs mb-1 ${isWriting ? 'text-gray-400' : isCorrect ? 'text-green-600' : 'text-red-500'}`}>
                Your answer
              </p>
              <p className={`text-sm whitespace-pre-wrap ${isWriting ? 'text-gray-700' : isCorrect ? 'text-green-800' : 'text-red-700'}`}>
                {answer || <span className="italic text-gray-400">No answer</span>}
              </p>
            </div>
            {isWrong && exercise.answer && (
              <div className="rounded-lg px-3 py-2 bg-green-50 border border-green-200">
                <p className="text-xs text-green-600 mb-1">Correct answer</p>
                <p className="text-sm text-green-800">{exercise.answer}</p>
              </div>
            )}
          </div>
        )
      })()}
    </div>
  )
}

export default function PracticePage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('vocai_user'))

  const [exercises, setExercises] = useState([])
  const [answers, setAnswers] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const raw = localStorage.getItem('vocai_current_lesson')
    if (raw) {
      const lesson = JSON.parse(raw)
      const exs = lesson?.content?.exercises || []
      setExercises(exs)
      setAnswers(Array(exs.length).fill(''))
    } else {
      setError('Lesson data not found. Please go back to the lesson page.')
    }
  }, [])

  function handleAnswerChange(index, value) {
    setAnswers((prev) => prev.map((a, i) => (i === index ? value : a)))
  }

  async function handleSubmit() {
    const filled = answers.filter((a) => a.trim())
    if (filled.length === 0) return
    setSubmitting(true)
    try {
      const res = await api.submitPractice(sessionId, user.user_id, answers)
      setResult(res)
      setSubmitted(true)
      // Level atlandıysa localStorage'ı güncelle
      if (res.level_up_applied) {
        const newLevel = res.level_up_applied.split('→').pop().trim()
        const updatedUser = { ...user, cefr_level: newLevel }
        localStorage.setItem('vocai_user', JSON.stringify(updatedUser))
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  function handleNextLesson() {
    localStorage.removeItem('vocai_current_lesson')
    navigate('/lesson')
  }

  const evaluation = result?.evaluation || {}
  const progress = result?.progress || {}
  const feedback = evaluation.feedback || ''
  // Toplam 10 egzersiz üzerinden hesapla — writing_prompt 0 doğru sayılır
  const totalQuestions = exercises.length
  const correctAnswers = exercises.reduce((count, ex, i) => {
    if (ex.type === 'writing_prompt') return count
    const userAnswer = (answers[i] || '').trim().toLowerCase()
    const correct = (ex.answer || '').trim().toLowerCase()
    return count + (correct && userAnswer === correct ? 1 : 0)
  }, 0)
  const scorePercent = totalQuestions > 0 ? Math.round((correctAnswers / totalQuestions) * 100) : 0

  // Skora göre renk
  const scoreColor = scorePercent >= 80 ? 'text-green-600' : scorePercent >= 60 ? 'text-amber-500' : 'text-red-500'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <button onClick={() => navigate('/lesson')} className="text-sm text-gray-400 hover:text-gray-600">
          ← Back
        </button>
        <h1 className="text-lg font-semibold text-brand-600">Practice</h1>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-lg">{user.cefr_level}</span>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        {error && !submitted && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-center">
            <p className="text-red-600 text-sm">{error}</p>
            <button onClick={() => navigate('/lesson')} className="mt-2 text-sm text-brand-600 hover:underline">
              Back to lesson
            </button>
          </div>
        )}

        {/* Exercises */}
        {exercises.length > 0 && (
          <div className="space-y-5 mb-8">
            {exercises.map((ex, i) => (
              <ExerciseCard
                key={i}
                exercise={ex}
                index={i}
                answer={answers[i] || ''}
                onChange={handleAnswerChange}
                submitted={submitted}
              />
            ))}
          </div>
        )}

        {/* Submit button */}
        {!submitted && exercises.length > 0 && (
          <button
            onClick={handleSubmit}
            disabled={submitting || answers.every((a) => !a.trim())}
            className="w-full bg-brand-600 text-white rounded-xl py-3 text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition"
          >
            {submitting ? 'Evaluating...' : 'Submit Answers'}
          </button>
        )}

        {/* Results */}
        {submitted && result && (
          <div className="space-y-5 mt-2">
            {/* Score card */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-gray-900">Results</h2>
                <div>
                  <span className={`text-3xl font-bold ${scoreColor}`}>{scorePercent}</span>
                  <span className="text-lg text-gray-400">/100</span>
                </div>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden mb-3">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    scorePercent >= 80 ? 'bg-green-500' : scorePercent >= 60 ? 'bg-amber-400' : 'bg-red-400'
                  }`}
                  style={{ width: `${scorePercent}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 text-center">
                {correctAnswers} / {totalQuestions} correct
              </p>
            </div>

            {/* Feedback */}
            {feedback && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-3">Feedback</h3>
                <p className="text-sm text-gray-700 leading-relaxed">{feedback}</p>
              </div>
            )}

            {/* Tebrik — level atlandı */}
            {result.level_up_applied && (
              <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border border-amber-200 rounded-2xl p-6 text-center shadow-sm">
                <p className="text-3xl mb-2">🎉</p>
                <p className="text-lg font-bold text-amber-800 mb-1">
                  {result.congratulations_message || `Tebrikler! ${result.level_up_applied} seviyesine ulaştın.`}
                </p>
                <p className="text-sm text-amber-600">
                  New lessons suited to your level are waiting for you.
                </p>
              </div>
            )}

            {/* Level up onay aşaması */}
            {!result.level_up_applied && progress.level_up_recommendation && (() => {
              // "B1 → B2" formatından hedef seviyeyi çıkar
              const target = progress.level_up_recommendation.split('→').pop().trim()
              return (
                <div className="bg-green-50 border border-green-200 rounded-2xl p-5">
                  <p className="text-sm text-green-800 font-semibold mb-1">🏆 You're ready to level up!</p>
                  <p className="text-sm text-green-700 mb-4">
                    Your performance suggests you're ready for <strong>{target}</strong>.
                    Take a short 3-question test to confirm.
                  </p>
                  <button
                    onClick={() => navigate(`/levelup?target=${target}`)}
                    className="w-full bg-green-600 text-white rounded-xl py-2.5 text-sm font-medium hover:bg-green-700 transition"
                  >
                    Take Level-Up Test → {target}
                  </button>
                </div>
              )
            })()}

            <div className="flex gap-3">
              <button
                onClick={() => navigate('/profile')}
                className="flex-1 border border-brand-600 text-brand-600 rounded-xl py-3 text-sm font-medium hover:bg-brand-50 transition"
              >
                My Profile
              </button>
              <button
                onClick={handleNextLesson}
                className="flex-1 bg-brand-600 text-white rounded-xl py-3 text-sm font-medium hover:bg-brand-700 transition"
              >
                Next Lesson →
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
