import { nextTick } from 'vue'
import { Mock, afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('gsap', () => {
  const kill = vi.fn()
  const tween = { kill }
  return {
    gsap: {
      set: vi.fn(),
      to: vi.fn(() => tween)
    }
  }
})

import { gsap } from 'gsap'
import AnimatedContent from '@/components/AnimatedContent.vue'

afterEach(() => {
  vi.clearAllMocks()
})

describe('AnimatedContent', () => {
  it('applies initial transform on mount and animates into view', async () => {
    const wrapper = mount(AnimatedContent, {
      slots: {
        default: '<div class="inner">Hello</div>'
      },
      props: {
        distance: 80,
        direction: 'vertical',
        animateOpacity: true
      }
    })

    await nextTick()

    expect(gsap.set).toHaveBeenCalledWith(expect.any(HTMLElement), expect.objectContaining({
      y: -80,
      opacity: 0
    }))

    expect(gsap.to).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      expect.objectContaining({
        y: 0,
        duration: 0.8,
        ease: 'power3.out'
      })
    )

    wrapper.unmount()
  })

  it('replays animation when reactive props change', async () => {
    const wrapper = mount(AnimatedContent, {
      slots: {
        default: '<div>Content</div>'
      }
    })

    await nextTick()
    const toMock = gsap.to as Mock
    const initialCalls = toMock.mock.calls.length

    await wrapper.setProps({ distance: 120 })
    await nextTick()
    const newCalls = toMock.mock.calls.length
    expect(newCalls).toBeGreaterThan(initialCalls)

    wrapper.unmount()
  })
})
