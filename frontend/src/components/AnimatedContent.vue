<template>
  <div ref="root" class="animated-content">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { gsap } from 'gsap'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const emit = defineEmits<{
  (event: 'complete'): void
}>()

const props = withDefaults(
  defineProps<{
    distance?: number
    direction?: 'vertical' | 'horizontal'
    reverse?: boolean
    duration?: number
    ease?: string
    initialOpacity?: number
    animateOpacity?: boolean
    scale?: number
    threshold?: number
    delay?: number
    once?: boolean
  }>(),
  {
    distance: 100,
    direction: 'vertical',
    reverse: false,
    duration: 0.8,
    ease: 'power3.out',
    initialOpacity: 0,
    animateOpacity: true,
    scale: 1,
    threshold: 0.1,
    delay: 0,
    once: false,
  }
)

const axis = computed(() => (props.direction === 'horizontal' ? 'x' : 'y'))
const offset = computed(() => (props.reverse ? props.distance : -props.distance))

const root = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null
let tween: gsap.core.Tween | null = null
let hasPlayed = false

const stopAnimation = () => {
  if (tween) {
    tween.kill()
    tween = null
  }
}

const setInitialState = () => {
  if (!root.value) return
  const initialVars: gsap.TweenVars = {
    [axis.value]: offset.value,
    willChange: 'transform, opacity',
  }

  if (props.animateOpacity) {
    initialVars.opacity = props.initialOpacity
  }
  if (props.scale !== 1) {
    initialVars.scale = props.scale
  }

  gsap.set(root.value, initialVars)
}

const runAnimation = () => {
  if (!root.value) return

  stopAnimation()
  hasPlayed = true

  const toVars: gsap.TweenVars = {
    [axis.value]: 0,
    duration: props.duration,
    ease: props.ease,
    delay: props.delay,
    onComplete: () => {
      root.value?.style.removeProperty('will-change')
      emit('complete')
    },
  }

  if (props.animateOpacity) {
    toVars.opacity = 1
  }
  if (props.scale !== 1) {
    toVars.scale = 1
  }

  tween = gsap.to(root.value, toVars)
}

const handleIntersect: IntersectionObserverCallback = (entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return
    if (props.once && hasPlayed) return
    runAnimation()

    if (props.once && observer && root.value) {
      observer.unobserve(root.value)
      observer.disconnect()
      observer = null
    }
  })
}

const setupObserver = () => {
  if (!root.value) return

  if (typeof IntersectionObserver === 'undefined') {
    nextTick(runAnimation)
    return
  }

  observer = new IntersectionObserver(handleIntersect, {
    threshold: Math.min(Math.max(props.threshold, 0), 1),
  })
  observer.observe(root.value)
}

const resetAndReplay = () => {
  stopAnimation()
  hasPlayed = false
  setInitialState()

  if (observer && root.value) {
    observer.unobserve(root.value)
    observer.observe(root.value)
    return
  }

  if (!observer && root.value) {
    setupObserver()
    return
  }

  if (!observer) {
    nextTick(runAnimation)
  }
}

onMounted(() => {
  nextTick(() => {
    setInitialState()
    setupObserver()
  })
})

onBeforeUnmount(() => {
  stopAnimation()
  if (observer && root.value) {
    observer.unobserve(root.value)
    observer.disconnect()
    observer = null
  }
})

watch(
  () => [
    props.distance,
    props.direction,
    props.reverse,
    props.scale,
    props.animateOpacity,
    props.initialOpacity,
    props.duration,
    props.delay,
  ],
  () => resetAndReplay()
)
</script>

<style scoped>
.animated-content {
  display: block;
  width: 100%;
  flex: 1 1 auto;
  min-width: 0;
}
</style>
