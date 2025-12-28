<template>
  <div ref="root" class="animated-content">
    <slot />
  </div>
</template>

<script setup>
import { gsap } from 'gsap'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const emit = defineEmits(['complete'])

const props = defineProps({
  distance: { type: Number, default: 100 },
  direction: { type: String, default: 'vertical' },
  reverse: { type: Boolean, default: false },
  duration: { type: Number, default: 0.8 },
  ease: { type: String, default: 'power3.out' },
  initialOpacity: { type: Number, default: 0 },
  animateOpacity: { type: Boolean, default: true },
  scale: { type: Number, default: 1 },
  threshold: { type: Number, default: 0.1 },
  delay: { type: Number, default: 0 },
  once: { type: Boolean, default: false }
})

const axis = computed(() => (props.direction === 'horizontal' ? 'x' : 'y'))
const offset = computed(() => (props.reverse ? props.distance : -props.distance))

const root = ref(null)
let observer = null
let tween = null
let hasPlayed = false

const stopAnimation = () => {
  if (tween) {
    tween.kill()
    tween = null
  }
}

const setInitialState = () => {
  if (!root.value) return
  const initialVars = {
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

  const toVars = {
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

const handleIntersect = (entries) => {
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
