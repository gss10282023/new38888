import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { http, HttpResponse } from 'msw'

import { useAuthStore } from '@/stores/auth'
import { useGroupStore } from '@/stores/groups'
import { server } from '../mocks/server'

const API_BASE = 'http://127.0.0.1:8000/api'

describe('groups store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    const auth = useAuthStore()
    auth.setSession({
      user: { id: 99, email: 'student@example.com', name: 'Student', role: 'student' },
      accessToken: 'token',
      refreshToken: 'refresh'
    })
  })

  it('fetches and caches my groups', async () => {
    server.use(
      http.get(`${API_BASE}/groups/my-groups/`, () =>
        HttpResponse.json({
          groups: [
            { id: 'BTF001', name: 'Genome Explorers', members: 3, status: 'active', mentor: null }
          ]
        })
      )
    )

    const store = useGroupStore()
    const groups = await store.fetchMyGroups()

    expect(groups).toHaveLength(1)
    expect(store.groupsById['BTF001'].name).toBe('Genome Explorers')

    // Subsequent call is served from cache
    const cached = await store.fetchMyGroups()
    expect(cached).toHaveLength(1)
  })

  it('loads group detail and allows task lifecycle updates', async () => {
    server.use(
      http.get(`${API_BASE}/groups/BTF001/`, () =>
        HttpResponse.json({
          id: 'BTF001',
          name: 'Genome Explorers',
          status: 'active',
          track: 'AUS-NSW',
          members: [],
          milestones: [
            {
              id: 10,
              title: 'Sprint',
              description: 'Initial tasks',
              order_index: 1,
              tasks: [{ id: 5, name: 'Submit brief', completed: false }]
            }
          ]
        })
      ),
      http.post(`${API_BASE}/groups/BTF001/milestones/`, async ({ request }) => {
        const body = await request.json()
        expect(body.title).toBe('Deliverable')
        return HttpResponse.json({ id: 11, title: body.title, description: body.description, tasks: [] })
      }),
      http.post(`${API_BASE}/groups/BTF001/milestones/10/tasks/`, async ({ request }) => {
        const body = await request.json()
        expect(body.name).toBe('Draft slides')
        return HttpResponse.json({ id: 6, name: body.name, completed: false })
      }),
      http.put(`${API_BASE}/groups/BTF001/tasks/5/`, async ({ request }) => {
        const body = await request.json()
        expect(body.completed).toBe(true)
        return HttpResponse.json({ success: true, task: { id: 5, name: 'Submit brief', completed: true } })
      })
    )

    const store = useGroupStore()
    await store.fetchGroupDetail('BTF001')
    expect(store.groupsById['BTF001'].milestones).toHaveLength(1)

    await store.createMilestone('BTF001', { title: 'Deliverable', description: 'Prepare handout' })
    expect(store.groupsById['BTF001'].milestones).toHaveLength(2)

    await store.addTask('BTF001', 10, 'Draft slides')
    const tasks = store.groupsById['BTF001'].milestones[0].tasks
    expect(tasks).toHaveLength(2)

    await store.setTaskCompletion('BTF001', 5, true)
    expect(tasks.find((task) => task.id === 5)?.completed).toBe(true)
  })
})
