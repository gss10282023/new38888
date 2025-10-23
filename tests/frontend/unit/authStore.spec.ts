import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

import { useAuthStore } from '@/stores/auth'

const API_BASE = 'http://127.0.0.1:8000/api'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('requests magic link and stores pending email', async () => {
    const auth = useAuthStore()

    await auth.requestMagicLink('STUDENT@Example.Com')

    expect(auth.pendingEmail).toBe('student@example.com')
    expect(localStorage.getItem('auth.pendingEmail')).toBe('student@example.com')
  })

  it('verifies otp and persists session', async () => {
    server.use(
      http.post(`${API_BASE}/auth/verify-otp/`, async ({ request }) => {
        const body = await request.json()
        expect(body.email).toBe('student@example.com')
        return HttpResponse.json({
          token: 'access-token',
          refresh_token: 'refresh-token',
          user: { id: 1, email: 'student@example.com', name: 'Student', role: 'student' }
        })
      })
    )

    const auth = useAuthStore()
    auth.pendingEmail = 'student@example.com'

    await auth.verifyOtp('123456')

    expect(auth.user?.email).toBe('student@example.com')
    expect(auth.accessToken).toBe('access-token')
    expect(JSON.parse(localStorage.getItem('auth.session') || '{}').accessToken).toBe('access-token')
  })

  it('refreshes session when authenticated fetch returns 401', async () => {
    let firstCall = true
    server.use(
      http.post(`${API_BASE}/auth/refresh/`, () =>
        HttpResponse.json({ token: 'new-access', refresh_token: 'new-refresh' })
      ),
      http.get(`${API_BASE}/users/me/`, () => {
        if (firstCall) {
          firstCall = false
          return HttpResponse.text('Unauthorized', { status: 401 })
        }
        return HttpResponse.json({ id: 1, email: 'student@example.com', name: 'Student', role: 'student' })
      })
    )

    const auth = useAuthStore()
    auth.setSession({
      user: { id: 1, email: 'student@example.com', name: 'Student', role: 'student' },
      accessToken: 'expired-access',
      refreshToken: 'valid-refresh'
    })

    const response = await auth.authenticatedFetch('/users/me/')
    expect(response.status).toBe(200)
    expect(auth.accessToken).toBe('new-access')
  })
})
