<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth' // Pinia Auth
import { useGroupStore } from '@/stores/groups'
import { useResourceStore } from '@/stores/resources'
import { mockAnnouncements } from '../data/mock.js'

const router = useRouter()

// 从 Pinia 取当前登录用户与是否管理员
const auth = useAuthStore()
const { user, isAdmin } = storeToRefs(auth)
// 若 store 没有 isAdmin getter，则兜底判断 role
const effectiveIsAdmin = computed(() => (isAdmin?.value ?? (user.value?.role === 'admin')))

const groupStore = useGroupStore()
const { myGroups, loadingMyGroups, allGroups, loadingAllGroups } = storeToRefs(groupStore)
const groups = computed(() => myGroups.value || [])
const adminGroups = computed(() => allGroups.value || [])
const activeGroupCount = computed(() =>
  effectiveIsAdmin.value ? adminGroups.value.length : groups.value.length
)
const resourceStore = useResourceStore()
const { items: resourceItems, loadingList: loadingResources } = storeToRefs(resourceStore)
const resourcePreview = computed(() => (resourceItems.value || []).slice(0, 6))
const announcements = ref(mockAnnouncements)
const announcementsCount = computed(() => announcements.value.length)

const getCurrentDate = () =>
  new Date().toLocaleDateString('en-AU', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

const getResourceIcon = (type) => {
  const icons = {
    document: 'fas fa-file-alt',
    video: 'fas fa-video',
    link: 'fas fa-link',
    template: 'fas fa-file-code',
    guide: 'fas fa-book'
  }
  return icons[type] || 'fas fa-file'
}

const formatResourceUpdated = (resource) => {
  const value = resource?.updatedAt || resource?.updated_at
  if (!value) return '—'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return '—'
  return new Intl.DateTimeFormat('en-AU', { dateStyle: 'medium' }).format(parsed)
}

const resourceBannerStyle = (resource) => {
  const base =
    'height:100px; display:flex; align-items:center; justify-content:center; border-radius:8px; color:#fff;'
  if (resource?.coverImage) {
    return `${base} background-image:url('${resource.coverImage}'); background-size:cover; background-position:center;`
  }
  return `${base} background: linear-gradient(135deg, var(--dark-green), var(--eucalypt));`
}

const loadGroups = async (force = false) => {
  if (!auth.isAuthenticated) return
  const tasks = []
  if (effectiveIsAdmin.value) {
    tasks.push(groupStore.fetchAllGroups({ forceRefresh: force }))
  }
  tasks.push(groupStore.fetchMyGroups({ forceRefresh: force }))
  const results = await Promise.allSettled(tasks)
  results.forEach((result) => {
    if (result.status === 'rejected') {
      console.error('Failed to load groups', result.reason)
    }
  })
}

const loadResources = async (force = false) => {
  if (!auth.isAuthenticated) return
  try {
    await resourceStore.fetchResources({ forceRefresh: force })
  } catch (error) {
    console.error('Failed to load resources', error)
  }
}

onMounted(() => {
  loadGroups()
  loadResources()
})

watch(
  () => auth.isAuthenticated,
  (loggedIn) => {
    if (loggedIn) {
      loadGroups(true)
      loadResources(true)
    } else {
      groupStore.reset()
      resourceStore.reset()
    }
  }
)

watch(
  () => effectiveIsAdmin.value,
  (isAdminNow, wasAdmin) => {
    if (isAdminNow && !wasAdmin) {
      loadGroups(true)
      loadResources(true)
    }
  }
)
</script>

<template>
  <div class="content-area">
    <div style="margin-bottom: 2rem;">
      <h1>Welcome back, {{ user?.name || 'User' }}!</h1>
      <p style="color:#6c757d;">
        {{ getCurrentDate() }} - Track: {{ user?.track || '—' }}
      </p>
    </div>

    <div class="grid grid-3" style="margin-bottom: 2rem;">
      <!-- Active Groups：仅管理员可见 -->
      <div class="widget" v-if="effectiveIsAdmin">
        <div class="widget-header">
          <span class="widget-title">Active Groups</span>
          <i class="fas fa-users" style="color: var(--eucalypt);"></i>
        </div>
        <div class="widget-value">
          <span v-if="loadingMyGroups || loadingAllGroups">…</span>
          <span v-else>{{ activeGroupCount }}</span>
        </div>
        <div class="widget-footer">
          <RouterLink to="/groups" style="color: var(--dark-green);">View all groups →</RouterLink>
        </div>
      </div>

      <div class="widget">
        <div class="widget-header">
          <span class="widget-title">Upcoming Events</span>
          <i class="fas fa-calendar" style="color: var(--mint-green);"></i>
        </div>
        <div class="widget-value">3</div>
        <div class="widget-footer">
          <RouterLink to="/events" style="color: var(--dark-green);">View calendar →</RouterLink>
        </div>
      </div>

      <!-- Resources -> Recent Announcements -->
      <div class="widget">
        <div class="widget-header">
          <span class="widget-title">Recent Announcements</span>
          <i class="fas fa-bullhorn" style="color: var(--air-force-blue);"></i>
        </div>
        <div class="widget-value">{{ announcementsCount }}</div>
        <div class="widget-footer">
          <RouterLink to="/announcements" style="color: var(--dark-green);">
            View announcements →
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- My Active Groups：所有用户可见 -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          My Active Groups
          <span v-if="groups.length">({{ groups.length }})</span>
        </h3>
        <RouterLink to="/groups" style="color: var(--dark-green);">View all</RouterLink>
      </div>

      <div v-if="loadingMyGroups" class="empty-state">Loading your groups…</div>
      <div v-else-if="!groups.length" class="empty-state">You are not assigned to any groups yet.</div>
      <div v-else class="grid grid-2">
        <div
          v-for="group in groups"
          :key="group.id"
          class="group-card"
          @click="router.push('/groups/' + group.id)"
        >
          <div class="group-header">
            <div class="group-avatars">
              <div class="group-avatar">AP</div>
              <div class="group-avatar" style="background-color: var(--mint-green);">YG</div>
              <div class="group-avatar" style="background-color: var(--air-force-blue);">
                +{{ Math.max((group.members || 0) - 2, 0) }}
              </div>
            </div>
            <div class="group-info">
              <div class="group-name">{{ group.name }}</div>
              <!-- 胶囊样式的操作标签；.stop 防止触发整卡跳转 -->
              <!-- <button type="button" class="chip-action" @click.stop>
                {{ group.status }}
              </button> -->
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 资源区（所有用户可见） -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Learn more with resources</h3>
        <RouterLink to="/resources" style="color: var(--dark-green);">View all</RouterLink>
      </div>

      <div v-if="loadingResources" class="empty-state">Loading resources…</div>
      <div v-else-if="!resourcePreview.length" class="empty-state">No resources available yet.</div>
      <div v-else class="resource-grid">
        <div
          v-for="resource in resourcePreview"
          :key="resource.id"
          class="resource-card"
          @click="router.push('/resources/' + resource.id)"
        >
          <div class="resource-preview-banner" :style="resourceBannerStyle(resource)">
            <i v-if="!resource.coverImage" :class="getResourceIcon(resource.type)"></i>
          </div>
          <div class="resource-content">
            <div class="resource-title">{{ resource.title }}</div>
            <div class="resource-meta">Updated {{ formatResourceUpdated(resource) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 更精致的“Schedule Workshop”胶囊按钮 */
.chip-action {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1;
  border-radius: 999px;
  background-color: var(--light-green);
  color: var(--dark-green);
  border: 1px solid var(--dark-green);
  cursor: pointer;
  transition: all 0.2s ease;
}
.chip-action:hover {
  background-color: var(--dark-green);
  color: var(--white);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px var(--shadow);
}

.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #6c757d;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.resource-card {
  background: var(--white);
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(21, 30, 24, 0.08);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.resource-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(21, 30, 24, 0.12);
}

.resource-preview-banner {
  width: 100%;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--dark-green), var(--eucalypt));
}
.resource-preview-banner i {
  font-size: 1.8rem;
  opacity: 0.9;
}

.resource-content {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.resource-title {
  font-weight: 600;
  color: var(--charcoal);
}
.resource-meta {
  font-size: 0.85rem;
  color: #6c757d;
}
</style>
