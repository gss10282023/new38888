import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { http, HttpResponse } from 'msw'

import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'
import { server } from '../mocks/server'

const API_BASE = 'http://127.0.0.1:8000/api'

describe('admin store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.setSession({
      user: { id: 1, email: 'admin@example.com', role: 'admin', name: 'Admin' },
      accessToken: 'token',
      refreshToken: 'refresh'
    })
  })

  it('fetches stats with track filter and normalises state', async () => {
    server.use(
      http.get(`${API_BASE}/admin/stats/`, ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('track')).toBe('AUS-NSW')
        return HttpResponse.json({
          totalUsers: 10,
          activeGroups: 3,
          mentors: { total: 2, active: 2, pending: 0 },
          students: { total: 8, pending: 1 }
        })
      })
    )

    const store = useAdminStore()
    const stats = await store.fetchStats({ track: 'AUS-NSW' })

    expect(stats.totalUsers).toBe(10)
    expect(store.statsLoading).toBe(false)
    expect(store.stats?.students.pending).toBe(1)
  })

  it('fetches users and updates pagination metadata', async () => {
    server.use(
      http.get(`${API_BASE}/admin/users/`, ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('role')).toBe('student')
        return HttpResponse.json({
          count: 2,
          next: null,
          previous: null,
          results: [
            { id: 1, email: 'a@example.com', role: 'student', name: 'A', track: 'Global', status: 'active' },
            { id: 2, email: 'b@example.com', role: 'student', name: 'B', track: 'Global', status: 'pending' }
          ]
        })
      })
    )

    const store = useAdminStore()
    const users = await store.fetchUsers({ role: 'student' })

    expect(users).toHaveLength(2)
    expect(store.pagination.count).toBe(2)
    expect(store.filters.role).toBe('student')
  })

  it('loads filter options and caches them', async () => {
    server.use(
      http.get(`${API_BASE}/admin/users/filters/`, () =>
        HttpResponse.json({
          tracks: ['AUS-NSW'],
          roles: ['student', 'mentor'],
          statuses: ['active', 'pending']
        })
      )
    )

    const store = useAdminStore()
    const options = await store.fetchFilterOptions()

    expect(options.tracks).toContain('Global')
    expect(store.filterOptions.roles).toContain('mentor')

    // Subsequent call should reuse cached data
    const cached = await store.fetchFilterOptions()
    expect(cached).toBe(options)
  })
})

