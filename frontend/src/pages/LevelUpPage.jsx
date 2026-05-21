import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

function ChatBubble({ role, text }) {
  const isAI = role === 'ai'
  return (
    <div className={`flex ${isAI ? 'justify-start' : 'justify-end'} mb-3`}>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isAI
            ? 'bg-white border border-gray-100 text-gray-800 shadow-sm'
            : 'bg-brand-600 text-white'
        }`}
      >
        {text}
      </div>
    </div>
  )
}

export default function LevelUpPage() {
  const [searchParams] = useSearchParams()
  const targetLevel = searchParams.get('target') || 'B2'

  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [streaming, setStreaming] = useState(false)
  const [result, setResult] = useState(null) // { type: 'confirmed'|'failed', level }
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const navigate = useNavigate()

  const user = JSON.parse(localStorage.getItem('vocai_user'))

  useEffect(() => {
    api.startLevelUp(user.user_id, targetLevel)
      .then((res) => {
        setSessionId(res.session_id)
        setMessages([{ role: 'ai', text: res.initial_message }])
      })
      .catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    if (!input.trim() || streaming || !sessionId) return
    const userText = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: userText }])
    setStreaming(true)

    try {
      const res = await api.streamLevelUpMessage(sessionId, user.user_id, userText, targetLevel)
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let aiText = ''
      let aiIndex = null

      setMessages((prev) => {
        aiIndex = prev.length
        return [...prev, { role: 'ai', text: '' }]
      })

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop()

        for (const part of parts) {
          if (!part.startsWith('data: ')) continue
          const data = JSON.parse(part.slice(6))

          if (data.type === 'token') {
            aiText += data.content
            setMessages((prev) =>
              prev.map((m, i) => (i === aiIndex ? { ...m, text: aiText } : m))
            )
          } else if (data.type === 'level_up_confirmed') {
            setMessages((prev) =>
              prev.map((m, i) => (i === aiIndex ? { ...m, text: data.final_message } : m))
            )
            // localStorage güncelle
            const updated = { ...user, cefr_level: data.new_level }
            localStorage.setItem('vocai_user', JSON.stringify(updated))
            localStorage.removeItem('vocai_current_lesson')
            setResult({ type: 'confirmed', level: data.new_level })

          } else if (data.type === 'level_up_failed') {
            setMessages((prev) =>
              prev.map((m, i) => (i === aiIndex ? { ...m, text: data.final_message } : m))
            )
            setResult({ type: 'failed', level: data.current_level })
          }
        }
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-brand-600">VocAI</h1>
        <div className="text-sm text-gray-500 flex items-center gap-2">
          <span className="text-xs bg-brand-50 text-brand-600 font-semibold px-2 py-1 rounded-lg">
            {user.cefr_level}
          </span>
          <span>→</span>
          <span className="text-xs bg-green-50 text-green-700 font-semibold px-2 py-1 rounded-lg">
            {targetLevel}
          </span>
          <span className="text-gray-400 ml-1">Level-Up Test</span>
        </div>
      </header>

      {/* Info banner */}
      <div className="bg-brand-50 border-b border-brand-100 px-6 py-3 text-center">
        <p className="text-xs text-brand-700">
          Answer <strong>3 questions</strong> to prove you're ready for {targetLevel}.
          Be honest — this determines your actual level.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6 max-w-2xl w-full mx-auto">
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} text={m.text} />
        ))}
        {streaming && messages[messages.length - 1]?.text === '' && (
          <div className="flex justify-start mb-3">
            <div className="bg-white border border-gray-100 rounded-2xl px-4 py-3 shadow-sm">
              <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-bounce mr-1" />
              <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.15s] mr-1" />
              <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.3s]" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-center text-red-500 text-sm pb-2">{error}</p>}

      {/* Result buttons */}
      {result ? (
        <div className="p-4 max-w-2xl mx-auto w-full">
          {result.type === 'confirmed' ? (
            <div className="space-y-3">
              <div className="bg-green-50 border border-green-200 rounded-2xl p-4 text-center">
                <p className="text-2xl mb-1">🎉</p>
                <p className="font-semibold text-green-800">Level updated to {result.level}</p>
              </div>
              <button
                onClick={() => navigate('/lesson')}
                className="w-full bg-brand-600 text-white rounded-xl py-3 text-sm font-medium hover:bg-brand-700 transition"
              >
                Start {result.level} Lessons →
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-center">
                <p className="text-sm text-amber-800 font-medium">Not ready for {targetLevel} yet</p>
                <p className="text-xs text-amber-600 mt-1">Keep practicing — you'll get there!</p>
              </div>
              <button
                onClick={() => navigate('/lesson')}
                className="w-full bg-brand-600 text-white rounded-xl py-3 text-sm font-medium hover:bg-brand-700 transition"
              >
                Back to Lessons
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="p-4 max-w-2xl mx-auto w-full">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Type your answer..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              disabled={streaming}
              className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <button
              onClick={sendMessage}
              disabled={streaming || !input.trim()}
              className="bg-brand-600 text-white px-5 py-3 rounded-xl text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
