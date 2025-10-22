<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAnnouncementStore } from '@/stores/announcements'
import { useAuthStore } from '@/stores/auth'

const q = ref('')

const auth = useAuthStore()
const { isAuthenticated, isAdmin, user } = storeToRefs(auth)

const announcementStore = useAnnouncementStore()
const { items, loadingList, listError, creating } = storeToRefs(announcementStore)

const showCreateForm = ref(false)
const formError = ref(null)
const formState = ref({
  title: '',
  summary: '',
  content: '',
  author: '',
  audience: 'all',
  link: '',
})

const audienceOptions = [
  { value: 'all', label: 'All Users' },
  { value: 'student', label: 'Student' },
  { value: 'mentor', label: 'Mentor' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'admin', label: 'Admin' },
]

const canCreateAnnouncements = computed(() => isAdmin?.value ?? false)

const filtered = computed(() => {
  const text = q.value.trim().toLowerCase()
  const source = items.value || []
  if (!text) return source
  return source.filter((announcement) =>
    [announcement.title, announcement.summary, announcement.author]
      .some((field) => String(field || '').toLowerCase().includes(text))
  )
})

const errorMessage = computed(() => {
  const error = listError.value
  if (!error) return null
  return error.message || String(error)
})

const resetForm = () => {
  formState.value = {
    title: '',
    summary: '',
    content: '',
    author: user.value?.name || 'Program Team',
    audience: 'all',
    link: '',
  }
  formError.value = null
}

const loadAnnouncements = async (force = false) => {
  if (!isAuthenticated.value) return
  try {
    await announcementStore.fetchAnnouncements({ forceRefresh: force })
  } catch (error) {
    console.error('Failed to load announcements', error)
  }
}

onMounted(() => {
  resetForm()
  loadAnnouncements()
})

watch(isAuthenticated, (loggedIn) => {
  if (loggedIn) {
    loadAnnouncements(true)
  } else {
    announcementStore.reset()
  }
})

watch(
  () => user.value?.name,
  (name) => {
    if (!showCreateForm.value) {
      formState.value.author = name || 'Program Team'
    }
  }
)

const toggleCreateForm = () => {
  showCreateForm.value = !showCreateForm.value
  if (!showCreateForm.value) {
    resetForm()
  }
}

const handleCreate = async () => {
  formError.value = null
  const payload = {
    title: formState.value.title.trim(),
    summary: formState.value.summary.trim(),
    content: formState.value.content.trim(),
    author: formState.value.author.trim() || undefined,
    audience: formState.value.audience,
    link: formState.value.link.trim() || undefined,
  }

  if (!payload.title) {
    formError.value = 'Title is required'
    return
  }
  if (!payload.summary) {
    formError.value = 'Summary is required'
    return
  }

  try {
    await announcementStore.createAnnouncement(payload)
    resetForm()
    showCreateForm.value = false
  } catch (error) {
    formError.value = error?.message || 'Failed to create announcement'
  }
}

const formatDate = (iso) => {
  if (!iso) return '—'
  const parsed = new Date(iso)
  if (Number.isNaN(parsed.getTime())) return '—'
  return parsed.toLocaleDateString('en-AU', { year: 'numeric', month: 'short', day: 'numeric' })
}

const getAudienceLabel = (audience) => {
  const labels = {
    all: 'All Users',
    student: 'Student',
    mentor: 'Mentor',
    supervisor: 'Supervisor',
    admin: 'Admin',
  }
  return labels[audience] || 'Unknown'
}

const getAudienceClass = (audience) => {
  const classes = {
    all: 'status-active',
    student: 'status-info',
    mentor: 'status-warning',
    supervisor: 'status-pending',
    admin: 'status-danger',
  }
  return classes[audience] || 'status-active'
}
</script>

<template>
  <div class="content-area">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem;">
      <h1>Recent Announcements</h1>
      <div style="display:flex;gap:0.75rem;align-items:center;">
        <input
          v-model="q"
          type="text"
          class="form-control"
          placeholder="Search announcements..."
          style="width: 320px;"
        />
        <button
          v-if="canCreateAnnouncements"
          type="button"
          class="btn btn-primary"
          @click="toggleCreateForm"
        >
          {{ showCreateForm ? 'Cancel' : 'New Announcement' }}
        </button>
      </div>
    </div>

    <div v-if="canCreateAnnouncements && showCreateForm" class="card" style="margin-bottom:1.5rem;">
      <form @submit.prevent="handleCreate">
        <div class="form-group">
          <label class="form-label">Title</label>
          <input
            v-model="formState.title"
            type="text"
            class="form-control"
            placeholder="Announcement title"
            required
          />
        </div>

        <div class="form-group" style="margin-top:1rem;">
          <label class="form-label">Summary</label>
          <textarea
            v-model="formState.summary"
            class="form-control"
            rows="2"
            placeholder="Short summary shown in the list"
            required
          />
        </div>

        <div class="form-group" style="margin-top:1rem;">
          <label class="form-label">Content (optional)</label>
          <textarea
            v-model="formState.content"
            class="form-control"
            rows="4"
            placeholder="Full announcement content"
          />
        </div>

        <div class="form-group" style="display:flex;gap:1rem;margin-top:1rem;flex-wrap:wrap;">
          <div style="flex:1;min-width:220px;">
            <label class="form-label">Audience</label>
            <select v-model="formState.audience" class="form-control">
              <option v-for="option in audienceOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <div style="flex:1;min-width:220px;">
            <label class="form-label">Author (optional)</label>
            <input
              v-model="formState.author"
              type="text"
              class="form-control"
              placeholder="Display name for this announcement"
            />
          </div>
        </div>

        <div class="form-group" style="margin-top:1rem;">
          <label class="form-label">Link (optional)</label>
          <input
            v-model="formState.link"
            type="url"
            class="form-control"
            placeholder="https://example.com/more-info"
          />
        </div>

        <p v-if="formError" style="color:#c0392b;margin-top:1rem;">{{ formError }}</p>

        <div style="display:flex;justify-content:flex-end;gap:0.75rem;margin-top:1.5rem;">
          <button type="button" class="btn btn-outline" @click="toggleCreateForm">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="creating">
            {{ creating ? 'Creating…' : 'Create Announcement' }}
          </button>
        </div>
      </form>
    </div>

    <div v-if="loadingList" class="card">
      <p style="margin:0;color:#6c757d;">Loading announcements…</p>
    </div>

    <div v-else-if="errorMessage" class="card">
      <p style="margin:0;color:#c0392b;">{{ errorMessage }}</p>
    </div>

    <template v-else>
      <div class="card" v-for="a in filtered" :key="a.id" style="margin-bottom:1rem;">
        <div class="card-header" style="margin-bottom:0;padding-bottom:0;border-bottom:none;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <h3 class="card-title" style="margin:0;">{{ a.title }}</h3>
            <span class="status-badge" :class="getAudienceClass(a.audience)">
              {{ getAudienceLabel(a.audience) }}
            </span>
          </div>
        </div>
        <div style="color:#6c757d;margin:0.25rem 0 1rem;">
          {{ formatDate(a.createdAt || a.date) }} · {{ a.author || 'Program Team' }}
        </div>
        <p style="margin-bottom:1rem;line-height:1.7;">{{ a.summary }}</p>

        <div>
          <RouterLink v-if="a.route" :to="a.route" class="btn btn-outline btn-sm">Read more</RouterLink>
          <a
            v-else-if="a.link"
            :href="a.link"
            target="_blank"
            rel="noopener"
            class="btn btn-outline btn-sm"
          >
            Open link
          </a>
        </div>
      </div>

      <div v-if="filtered.length === 0" class="card">
        <p style="margin:0;color:#6c757d;">No announcements found.</p>
      </div>
    </template>
  </div>
</template>
