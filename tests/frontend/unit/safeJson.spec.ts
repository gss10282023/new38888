import { describe, expect, it } from 'vitest'

import { safeJson } from '@/utils/http'

describe('safeJson utility', () => {
  it('returns parsed JSON when available', async () => {
    const response = new Response(JSON.stringify({ ok: true }), {
      headers: { 'Content-Type': 'application/json' }
    })
    expect(await safeJson(response)).toEqual({ ok: true })
  })

  it('returns null on invalid content', async () => {
    const response = new Response('not-json', { status: 200 })
    expect(await safeJson(response)).toBeNull()
  })

  it('returns null for 204 responses', async () => {
    const response = new Response(null, { status: 204 })
    expect(await safeJson(response)).toBeNull()
  })
})

