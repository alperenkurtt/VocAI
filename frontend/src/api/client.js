const BASE = '/v1'

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'İstek başarısız')
  }
  return res.json()
}

export const api = {
  register: (username, password) =>
    request('POST', '/users/register', { username, password }),

  login: (username, password) =>
    request('POST', '/users/login', { username, password }),

  getUser: (userId) => request('GET', `/users/${userId}`),

  startAssessment: (userId) =>
    request('POST', '/assessment/start', { user_id: userId }),

  // SSE stream — caller handles the ReadableStream
  streamMessage: (sessionId, userId, message) =>
    fetch(`${BASE}/assessment/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, user_id: userId, message }),
    }),

  getTodayLesson: (userId) =>
    request('GET', `/lesson/today?user_id=${userId}`),

  submitPractice: (sessionId, userId, answers) =>
    request('POST', '/practice/submit', {
      session_id: sessionId,
      user_id: userId,
      answers,
    }),

  startLevelUp: (userId, targetLevel) =>
    request('POST', '/assessment/levelup/start', {
      user_id: userId,
      target_level: targetLevel,
    }),

  streamLevelUpMessage: (sessionId, userId, message, targetLevel) =>
    fetch(`${BASE}/assessment/levelup/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        user_id: userId,
        message,
        target_level: targetLevel,
      }),
    }),
}
