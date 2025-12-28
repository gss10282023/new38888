import { http, HttpResponse } from 'msw'
import {
  createAccessToken,
  createDemoState,
  createRefreshToken,
  getDemoUserByRole,
  parseUserIdFromToken
} from './demoData'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}

const withCors = (init = {}) => ({
  ...init,
  headers: {
    ...corsHeaders,
    ...(init.headers || {})
  }
})

const json = (data, init = {}) => HttpResponse.json(data, withCors(init))

const text = (data, init = {}) => new HttpResponse(data, withCors(init))

const state = createDemoState()

const getAuthUser = (request) => {
  const raw = request.headers.get('authorization') || request.headers.get('Authorization') || ''
  const match = raw.match(/^Bearer\s+(.+)$/i)
  if (!match) return null
  const token = match[1]
  const userId = parseUserIdFromToken(token)
  if (!userId) return null
  return state.users.find((u) => u.id === userId) || null
}

const ensureAdmin = (request) => {
  const user = getAuthUser(request)
  if (!user) {
    return { ok: false, response: json({ error: 'Unauthorized' }, { status: 401 }) }
  }
  if (user.role !== 'admin') {
    return { ok: false, response: json({ error: 'Forbidden' }, { status: 403 }) }
  }
  return { ok: true, user }
}

const groupSummaries = () =>
  Object.values(state.groupsById).map((group) => ({
    id: group.id,
    name: group.name,
    status: group.status,
    track: group.track,
    mentor: group.mentor ? { id: group.mentor.id, name: group.mentor.name } : null,
    members: Array.isArray(group.members) ? group.members.length : 0
  }))

const getMyGroupSummaries = (user) => {
  if (!user) return []
  if (user.role === 'admin') return groupSummaries()

  return Object.values(state.groupsById)
    .filter((group) => {
      if (group.mentor?.id && group.mentor.id === user.id) return true
      if (Array.isArray(group.members) && group.members.some((m) => m.id === user.id)) return true
      return false
    })
    .map((group) => ({
      id: group.id,
      name: group.name,
      status: group.status,
      track: group.track,
      mentor: group.mentor ? { id: group.mentor.id, name: group.mentor.name } : null,
      members: Array.isArray(group.members) ? group.members.length : 0
    }))
}

const resolveGroup = (groupId) => state.groupsById[groupId] || null

const nextId = (key) => {
  state.nextIds[key] = (state.nextIds[key] || 0) + 1
  return state.nextIds[key]
}

const parseJsonBody = async (request) => {
  try {
    return await request.json()
  } catch {
    return null
  }
}

const pickDemoRoleByEmail = (email) => {
  const value = String(email || '').toLowerCase()
  if (value.includes('admin')) return 'admin'
  if (value.includes('mentor')) return 'mentor'
  if (value.includes('supervisor')) return 'supervisor'
  if (value.includes('student')) return 'student'
  return 'student'
}

const applyUserPatch = (user, payload) => {
  if (!user || !payload) return user
  const next = { ...user }
  if (payload.track !== undefined) next.track = payload.track || ''
  if (payload.name !== undefined && payload.name) next.name = payload.name

  if (payload.profile && typeof payload.profile === 'object') {
    next.profile = { ...(next.profile || {}), ...payload.profile }
    const first = String(next.profile.firstName || '').trim()
    const last = String(next.profile.lastName || '').trim()
    const combined = `${first} ${last}`.trim()
    if (combined) next.name = combined
  }

  return next
}

export const handlers = [
  http.options('*', () => new HttpResponse(null, withCors({ status: 200 }))),

  // Auth
  http.post('*/api/auth/magic-link/', async ({ request }) => {
    const body = await parseJsonBody(request)
    const email = String(body?.email || '').trim().toLowerCase()
    if (!email) {
      return json({ error: 'Email is required' }, { status: 400 })
    }
    return json({ message: 'Demo mode: magic link sent (not really).' })
  }),

  http.post('*/api/auth/verify-otp/', async ({ request }) => {
    const body = await parseJsonBody(request)
    const email = String(body?.email || '').trim().toLowerCase()
    const code = String(body?.code || '').trim()
    if (!email) return json({ error: 'Email is required' }, { status: 400 })
    if (code.length !== 6) return json({ error: 'Invalid code' }, { status: 400 })

    const role = pickDemoRoleByEmail(email)
    const userTemplate = state.users.find((u) => u.email.toLowerCase() === email) || getDemoUserByRole(role)
    const user = { ...userTemplate, email }
    state.users = state.users.map((existing) => (existing.id === user.id ? { ...existing, email } : existing))
    const accessToken = createAccessToken(user.id)
    const refreshToken = createRefreshToken(user.id)

    return json({
      user,
      token: accessToken,
      refresh_token: refreshToken
    })
  }),

  http.post('*/api/auth/refresh/', async ({ request }) => {
    const body = await parseJsonBody(request)
    const refresh = String(body?.refresh_token || '')
    const userId = parseUserIdFromToken(refresh)
    if (!userId) {
      return json({ error: 'Invalid refresh token' }, { status: 401 })
    }
    return json({
      token: createAccessToken(userId),
      refresh_token: createRefreshToken(userId)
    })
  }),

  // Current user
  http.get('*/api/users/me/', ({ request }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    return json(user)
  }),

  http.put('*/api/users/me/', async ({ request }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    const payload = await parseJsonBody(request)
    const updated = applyUserPatch(user, payload)
    state.users = state.users.map((u) => (u.id === user.id ? updated : u))
    return json(updated)
  }),

  // Groups
  http.get('*/api/groups/my-groups/', ({ request }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    return json({ groups: getMyGroupSummaries(user) })
  }),

  http.get('*/api/groups/', ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response
    return json({ groups: groupSummaries() })
  }),

  http.post('*/api/groups/', async ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response
    const payload = await parseJsonBody(request)

    const name = String(payload?.name || '').trim()
    if (!name) return json({ error: 'Group name is required' }, { status: 400 })

    const id = String(payload?.groupId || '').trim() || `BTF${String(nextId('group')).padStart(3, '0')}`
    const track = String(payload?.track || '').trim() || 'Global'

    const mentorId = payload?.mentorId ?? null
    const mentor = mentorId
      ? state.users.find((u) => u.id === mentorId) || null
      : null

    const memberIds = Array.isArray(payload?.members)
      ? payload.members
          .map((m) => m?.userId)
          .filter((value) => Number.isFinite(Number(value)))
          .map((value) => Number(value))
      : []

    const members = memberIds
      .map((memberId) => {
        const found = state.users.find((u) => u.id === memberId)
        if (!found) return null
        return { id: found.id, name: found.name, role: found.role, email: found.email }
      })
      .filter(Boolean)

    const detail = {
      id,
      name,
      status: 'New',
      track,
      mentor: mentor ? { id: mentor.id, name: mentor.name, email: mentor.email } : null,
      members,
      milestones: []
    }

    state.groupsById[id] = detail
    state.messagesByGroup[id] = []

    return json({
      id,
      name,
      status: detail.status,
      track,
      mentor: detail.mentor ? { id: detail.mentor.id, name: detail.mentor.name } : null,
      members: members.length
    })
  }),

  http.get('*/api/groups/:groupId/', ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })

    const groupId = String(params.groupId || '')
    const group = resolveGroup(groupId)
    if (!group) return json({ error: 'Group not found' }, { status: 404 })

    if (user.role !== 'admin') {
      const isMentor = group.mentor?.id === user.id
      const isMember = Array.isArray(group.members) && group.members.some((m) => m.id === user.id)
      if (!isMentor && !isMember) {
        return json({ error: 'Forbidden' }, { status: 403 })
      }
    }

    return json(group)
  }),

  http.delete('*/api/groups/:groupId/', ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const groupId = String(params.groupId || '')
    if (!state.groupsById[groupId]) return new HttpResponse(null, withCors({ status: 204 }))

    delete state.groupsById[groupId]
    delete state.messagesByGroup[groupId]
    return new HttpResponse(null, withCors({ status: 204 }))
  }),

  http.put('*/api/groups/:groupId/tasks/:taskId/', async ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    const group = resolveGroup(String(params.groupId || ''))
    if (!group) return json({ error: 'Group not found' }, { status: 404 })

    const payload = await parseJsonBody(request)
    const completed = Boolean(payload?.completed)
    const taskId = String(params.taskId || '')

    group.milestones.forEach((milestone) => {
      const task = milestone.tasks?.find((t) => String(t.id) === taskId)
      if (task) task.completed = completed
    })

    return json({ task: { id: taskId, completed } })
  }),

  http.post('*/api/groups/:groupId/milestones/', async ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    const group = resolveGroup(String(params.groupId || ''))
    if (!group) return json({ error: 'Group not found' }, { status: 404 })

    const payload = await parseJsonBody(request)
    const title = String(payload?.title || '').trim()
    if (!title) return json({ error: 'Milestone title is required' }, { status: 400 })
    const description = String(payload?.description || '').trim()

    const milestone = {
      id: nextId('milestone'),
      title,
      description,
      order_index: group.milestones.length,
      tasks: []
    }
    group.milestones.push(milestone)

    return json(milestone, { status: 201 })
  }),

  http.delete('*/api/groups/:groupId/milestones/:milestoneId/', ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    const group = resolveGroup(String(params.groupId || ''))
    if (!group) return json({ error: 'Group not found' }, { status: 404 })

    const milestoneId = String(params.milestoneId || '')
    group.milestones = (group.milestones || []).filter((m) => String(m.id) !== milestoneId)

    return new HttpResponse(null, withCors({ status: 204 }))
  }),

  http.post('*/api/groups/:groupId/milestones/:milestoneId/tasks/', async ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    const group = resolveGroup(String(params.groupId || ''))
    if (!group) return json({ error: 'Group not found' }, { status: 404 })

    const payload = await parseJsonBody(request)
    const name = String(payload?.name || '').trim()
    if (!name) return json({ error: 'Task name is required' }, { status: 400 })

    const milestoneId = String(params.milestoneId || '')
    const milestone = (group.milestones || []).find((m) => String(m.id) === milestoneId)
    if (!milestone) return json({ error: 'Milestone not found' }, { status: 404 })

    const task = {
      id: nextId('task'),
      name,
      completed: false
    }
    milestone.tasks = Array.isArray(milestone.tasks) ? milestone.tasks : []
    milestone.tasks.push(task)

    return json(task, { status: 201 })
  }),

  // Chat
  http.get('*/api/groups/:groupId/messages', ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })

    const groupId = String(params.groupId || '')
    const messages = state.messagesByGroup[groupId] || []
    return json({ messages, hasMore: false })
  }),

  http.post('*/api/groups/:groupId/messages', async ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })

    const groupId = String(params.groupId || '')
    const payload = await parseJsonBody(request)
    const textValue = String(payload?.text || '').trim()
    const attachments = Array.isArray(payload?.attachments) ? payload.attachments : []
    const message = {
      id: nextId('message'),
      text: textValue,
      timestamp: new Date().toISOString(),
      author: { id: user.id, name: user.name },
      attachments: attachments.map((file, index) => ({
        id: `${Date.now()}-${index}`,
        url: file.url,
        filename: file.filename || 'Attachment',
        size: file.size ?? null,
        mime_type: file.mimeType || file.mime_type || 'application/octet-stream'
      })),
      moderation: { status: 'approved' }
    }

    state.messagesByGroup[groupId] = [...(state.messagesByGroup[groupId] || []), message]
    return json(message, { status: 201 })
  }),

  http.post('*/api/uploads/', async ({ request }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    try {
      const form = await request.formData()
      const file = form.get('file')
      const filename = file?.name || 'upload'
      const size = file?.size ?? null
      const mimeType = file?.type || 'application/octet-stream'
      const url = `https://example.org/demo/uploads/${encodeURIComponent(filename)}`
      return json({ url, filename, size, mimeType }, { status: 201 })
    } catch {
      return json({ error: 'Invalid upload' }, { status: 400 })
    }
  }),

  // Resources
  http.get('*/api/resources/', ({ request }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    return json({ count: state.resources.length, results: state.resources })
  }),

  http.post('*/api/resources/', async ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    try {
      const form = await request.formData()
      const title = String(form.get('title') || '').trim()
      if (!title) return json({ error: 'Title is required' }, { status: 400 })

      const resource = {
        id: nextId('resource'),
        title,
        description: String(form.get('description') || ''),
        type: String(form.get('type') || 'document'),
        role: String(form.get('role') || 'all'),
        file_url: `https://example.org/demo/resources/${encodeURIComponent(title)}.pdf`,
        cover_image: null,
        download_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      state.resources = [resource, ...state.resources]
      return json(resource, { status: 201 })
    } catch {
      return json({ error: 'Invalid form data' }, { status: 400 })
    }
  }),

  http.put('*/api/resources/:resourceId/cover/', async ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const resourceId = Number(params.resourceId)
    const target = state.resources.find((r) => r.id === resourceId)
    if (!target) return json({ error: 'Not found' }, { status: 404 })

    try {
      await request.formData()
    } catch {}

    const coverUrl = `https://picsum.photos/seed/resource-${resourceId}/640/360`
    target.cover_image = coverUrl
    target.updated_at = new Date().toISOString()
    return json({ coverImage: coverUrl })
  }),

  http.delete('*/api/resources/:resourceId/', ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const resourceId = Number(params.resourceId)
    state.resources = state.resources.filter((r) => r.id !== resourceId)
    return new HttpResponse(null, withCors({ status: 204 }))
  }),

  // Events
  http.get('*/api/events/', ({ request }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })

    return json({ count: state.events.length, results: state.events })
  }),

  http.post('*/api/events/', async ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const payload = await parseJsonBody(request)
    const title = String(payload?.title || '').trim()
    if (!title) return json({ error: 'Title is required' }, { status: 400 })

    const event = {
      id: nextId('event'),
      title,
      description: String(payload?.description || ''),
      long_description: String(payload?.longDescription || payload?.long_description || ''),
      date: String(payload?.date || ''),
      time: String(payload?.time || ''),
      location: String(payload?.location || ''),
      type: String(payload?.type || 'virtual'),
      cover_image: null,
      register_link: String(payload?.registerLink || payload?.register_link || ''),
      capacity: payload?.capacity ?? null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      registration_count: 0,
      is_registered: false
    }
    state.events = [event, ...state.events]
    return json(event, { status: 201 })
  }),

  http.put('*/api/events/:eventId/cover/', async ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const eventId = Number(params.eventId)
    const target = state.events.find((ev) => ev.id === eventId)
    if (!target) return json({ error: 'Not found' }, { status: 404 })

    try {
      await request.formData()
    } catch {}

    const coverUrl = `https://picsum.photos/seed/event-${eventId}/960/540`
    target.cover_image = coverUrl
    target.updated_at = new Date().toISOString()
    return json({ coverImage: coverUrl })
  }),

  http.post('*/api/events/:eventId/register/', ({ request, params }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })

    const eventId = Number(params.eventId)
    const target = state.events.find((ev) => ev.id === eventId)
    if (!target) return json({ error: 'Not found' }, { status: 404 })

    target.registration_count = (target.registration_count || 0) + 1
    target.is_registered = true
    return json({ message: 'Registered' })
  }),

  http.delete('*/api/events/:eventId/', ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const eventId = Number(params.eventId)
    state.events = state.events.filter((ev) => ev.id !== eventId)
    return new HttpResponse(null, withCors({ status: 204 }))
  }),

  // Announcements
  http.get('*/api/announcements/', ({ request }) => {
    const user = getAuthUser(request)
    if (!user) return json({ error: 'Unauthorized' }, { status: 401 })
    return json({ count: state.announcements.length, results: state.announcements })
  }),

  http.post('*/api/announcements/', async ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const payload = await parseJsonBody(request)
    const title = String(payload?.title || '').trim()
    const summary = String(payload?.summary || '').trim()
    if (!title) return json({ error: 'Title is required' }, { status: 400 })
    if (!summary) return json({ error: 'Summary is required' }, { status: 400 })

    const item = {
      id: nextId('announcement'),
      title,
      summary,
      content: String(payload?.content || ''),
      author: String(payload?.author || 'Program Team'),
      audience: String(payload?.audience || 'all'),
      link: String(payload?.link || ''),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    state.announcements = [item, ...state.announcements]
    return json(item, { status: 201 })
  }),

  // Admin
  http.get('*/api/admin/stats/', ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const url = new URL(request.url)
    const track = (url.searchParams.get('track') || 'Global').trim() || 'Global'
    const normalizedTrack = track.toLowerCase() === 'global' ? 'Global' : track
    const users = state.users.filter((u) => {
      if (normalizedTrack === 'Global') return true
      return String(u.track || '').toLowerCase() === normalizedTrack.toLowerCase()
    })

    const mentors = users.filter((u) => u.role === 'mentor')
    const students = users.filter((u) => u.role === 'student')
    const activeGroups = Object.values(state.groupsById).filter((group) => {
      if (normalizedTrack === 'Global') return true
      return String(group.track || '').toLowerCase() === normalizedTrack.toLowerCase()
    }).length

    return json({
      totalUsers: users.length,
      activeGroups,
      mentors: {
        total: mentors.length,
        active: mentors.filter((u) => u.status === 'active').length,
        pending: mentors.filter((u) => u.status === 'pending').length
      },
      students: {
        total: students.length,
        pending: students.filter((u) => u.status === 'pending').length
      }
    })
  }),

  http.get('*/api/admin/users/filters/', ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const tracks = Array.from(new Set(state.users.map((u) => u.track).filter(Boolean)))
    const roles = ['student', 'mentor', 'supervisor', 'admin']
    const statuses = ['active', 'pending', 'inactive']

    return json({ tracks, roles, statuses })
  }),

  http.get('*/api/admin/users/export/', ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const header = ['id', 'name', 'email', 'role', 'track', 'status']
    const rows = state.users.map((u) => [u.id, u.name, u.email, u.role, u.track || '', u.status])
    const csv = [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(','))
      .join('\n')

    return text(csv, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="users-export.csv"'
      }
    })
  }),

  http.get('*/api/admin/users/', ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const url = new URL(request.url)
    const role = (url.searchParams.get('role') || '').trim()
    const status = (url.searchParams.get('status') || '').trim()
    const track = (url.searchParams.get('track') || '').trim()
    const search = (url.searchParams.get('search') || '').trim().toLowerCase()
    const pageSize = Number(url.searchParams.get('page_size') || 50)

    let results = [...state.users]
    if (role) results = results.filter((u) => u.role === role)
    if (status) results = results.filter((u) => u.status === status)
    if (track) results = results.filter((u) => String(u.track || '').toLowerCase() === track.toLowerCase())
    if (search) {
      results = results.filter((u) =>
        [u.name, u.email].some((field) => String(field || '').toLowerCase().includes(search))
      )
    }

    const slice = Number.isFinite(pageSize) ? results.slice(0, pageSize) : results
    return json({
      count: results.length,
      next: null,
      previous: null,
      results: slice
    })
  }),

  http.get('*/api/admin/users/:userId/', ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const userId = Number(params.userId)
    const found = state.users.find((u) => u.id === userId)
    if (!found) return json({ error: 'Not found' }, { status: 404 })
    return json(found)
  }),

  http.post('*/api/admin/users/', async ({ request }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const payload = await parseJsonBody(request)
    const email = String(payload?.email || '').trim()
    if (!email) return json({ error: 'Email is required' }, { status: 400 })

    const role = String(payload?.role || 'student')
    const track = String(payload?.track || '')
    const name = String(payload?.name || email)
    const status = String(payload?.status || 'pending')

    const user = {
      id: nextId('user'),
      name,
      email,
      role,
      track,
      status,
      profile: {
        firstName: '',
        lastName: ''
      }
    }
    state.users = [...state.users, user]
    return json(user, { status: 201 })
  }),

  http.put('*/api/admin/users/:userId/', async ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const userId = Number(params.userId)
    const payload = await parseJsonBody(request)
    const existing = state.users.find((u) => u.id === userId)
    if (!existing) return json({ error: 'Not found' }, { status: 404 })

    const updated = {
      ...existing,
      ...payload,
      profile: {
        ...(existing.profile || {}),
        ...(payload?.profile || {})
      }
    }
    state.users = state.users.map((u) => (u.id === userId ? updated : u))
    return json(updated)
  }),

  http.put('*/api/admin/users/:userId/status/', async ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const userId = Number(params.userId)
    const payload = await parseJsonBody(request)
    const status = String(payload?.status || '')
    const existing = state.users.find((u) => u.id === userId)
    if (!existing) return json({ error: 'Not found' }, { status: 404 })
    if (!status) return json({ error: 'Status is required' }, { status: 400 })

    const updated = { ...existing, status }
    state.users = state.users.map((u) => (u.id === userId ? updated : u))
    return json({ user: updated })
  }),

  http.delete('*/api/admin/users/:userId/', ({ request, params }) => {
    const guard = ensureAdmin(request)
    if (!guard.ok) return guard.response

    const userId = Number(params.userId)
    state.users = state.users.filter((u) => u.id !== userId)
    return new HttpResponse(null, withCors({ status: 204 }))
  })
]
