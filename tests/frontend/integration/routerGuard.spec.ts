import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

describe('router navigation guards', () => {
  beforeEach(() => {
    vi.resetModules()
    setActivePinia(createPinia())
  })

  it('redirects unauthenticated users to login page', async () => {
    const { default: router } = await import('@/router/index.js')
    await router.replace('/login')
    await router.isReady()

    await router.push('/dashboard').catch(() => {})
    expect(router.currentRoute.value.fullPath).toBe('/login')
  })

  it('redirects authenticated users away from login page', async () => {
    const { default: router } = await import('@/router/index.js')
    const { useAuthStore } = await import('@/stores/auth')
    const auth = useAuthStore()
    auth.setSession({
      user: { id: 1, email: 'admin@example.com', name: 'Admin', role: 'admin' },
      accessToken: 'token',
      refreshToken: 'refresh'
    })

    await router.replace('/dashboard')
    await router.isReady()
    await router.push('/login')

    expect(router.currentRoute.value.fullPath).toBe('/dashboard')
  })
})
