import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const handlers = [
  http.post('http://127.0.0.1:8000/api/auth/magic-link/', async ({ request }) => {
    const body = await request.json()
    if (!body.email) {
      return HttpResponse.json({ error: 'Email is required.' }, { status: 400 })
    }
    return HttpResponse.json({ success: true, message: 'Magic link sent.' })
  })
]

export const server = setupServer(...handlers)

export function resetServerHandlers() {
  server.resetHandlers()
}
