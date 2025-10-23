import '@testing-library/jest-dom'
import { afterAll, afterEach, beforeAll } from 'vitest'

import { resetServerHandlers, server } from './mocks/server'

class MockIntersectionObserver {
  constructor(callback) {
    this.callback = callback
  }

  observe(element) {
    this.callback([{ isIntersecting: true, target: element }])
  }

  unobserve() {}
  disconnect() {}
}

if (!global.IntersectionObserver) {
  global.IntersectionObserver = MockIntersectionObserver
}

// Provide noop scrollTo for components that might call it
if (!global.scrollTo) {
  global.scrollTo = () => {}
}

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  resetServerHandlers()
})
afterAll(() => server.close())
