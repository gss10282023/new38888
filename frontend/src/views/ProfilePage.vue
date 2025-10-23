<template>
  <div class="content-area">
    <div v-if="!isAuthenticated" class="card" style="padding:2rem;">
      <h3 style="margin-bottom:0.5rem;">Please sign in</h3>
      <p style="margin:0;">Sign in to view and edit your profile.</p>
    </div>

    <div v-else class="card" style="overflow:hidden;padding:0;">
      <div class="profile-header">
        <div class="profile-avatar-large">{{ getInitials(displayName) }}</div>
        <h2 class="profile-name">{{ displayName }}</h2>
        <p class="profile-role">
          {{ capitalise(user?.role) }}
          <span v-if="user?.track"> • {{ user.track }}</span>
        </p>
      </div>

      <div class="profile-content">
        <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
        <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>

        <div v-if="loading" class="loading-state">Loading...</div>

        <template v-else>
          <!-- Personal Information -->
          <div class="profile-section">
            <h3 class="profile-section-title">Personal Information</h3>
            <div class="profile-grid">
              <div class="form-group">
                <label class="form-label">Email (read-only)</label>
                <input class="form-control" :value="user?.email" disabled>
              </div>
              <div class="form-group">
                <label class="form-label">Name</label>
                <div style="display:flex;gap:0.75rem;">
                  <input
                    v-model="form.profile.firstName"
                    class="form-control"
                    placeholder="First name"
                  >
                  <input
                    v-model="form.profile.lastName"
                    class="form-control"
                    placeholder="Last name"
                  >
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Role</label>
                <input class="form-control" :value="capitalise(user?.role)" disabled>
              </div>
              <div class="form-group">
                <label class="form-label">Track / Region</label>
                <input
                  v-model="form.track"
                  class="form-control"
                  placeholder="e.g. AUS-NSW"
                >
              </div>
              <div class="form-group">
                <label class="form-label">School Name</label>
                <input
                  v-model="form.profile.schoolName"
                  class="form-control"
                  placeholder="Enter your school name"
                >
              </div>
              <div class="form-group">
                <label class="form-label">Year Level</label>
                <input
                  v-model="yearLevelInput"
                  class="form-control"
                  placeholder="e.g. 11"
                >
              </div>
              <div class="form-group">
                <label class="form-label">Country</label>
                <input
                  v-model="form.profile.country"
                  class="form-control"
                  placeholder="Country"
                >
              </div>
              <div class="form-group">
                <label class="form-label">Region / State</label>
                <input
                  v-model="form.profile.region"
                  class="form-control"
                  placeholder="e.g. NSW"
                >
              </div>
            </div>
          </div>

          <!-- Interests -->
          <div class="profile-section">
            <h3 class="profile-section-title">Areas of Interest</h3>
            <div style="display:flex;flex-wrap:wrap;gap:0.5rem;">
              <span
                v-for="interest in form.profile.areasOfInterest"
                :key="interest"
                class="status-badge"
                style="background-color:var(--light-green);color:var(--dark-green);display:inline-flex;align-items:center;gap:0.4rem;"
              >
                {{ interest }}
                <button
                  class="chip-delete"
                  type="button"
                  @click="removeInterest(interest)"
                  aria-label="Remove interest"
                >×</button>
              </span>

              <div style="display:flex;gap:0.5rem;align-items:center;">
                <input
                  v-model="newInterest"
                  class="form-control"
                  placeholder="Add interest…"
                  style="width:220px;"
                  @keyup.enter="addInterest"
                >
                <button class="btn btn-outline btn-sm" type="button" @click="addInterest">+ Add</button>
              </div>
            </div>
          </div>

          <!-- Availability / Bio -->
          <div class="profile-section">
            <h3 class="profile-section-title">Bio & Availability</h3>
            <div class="form-group">
              <label class="form-label">Availability</label>
              <textarea
                v-model="form.profile.availability"
                class="form-control"
                rows="3"
                placeholder="e.g. Available on weekends and Wednesday evenings"
              />
            </div>
            <div class="form-group">
              <label class="form-label">Bio</label>
              <textarea
                v-model="form.profile.bio"
                class="form-control"
                rows="4"
                placeholder="Share your background, interests, or how you can help"
              />
            </div>
          </div>

          <div style="display:flex;justify-content:flex-end;gap:1rem;">
            <button class="btn btn-outline" type="button" :disabled="saving" @click="reset">Reset</button>
            <button class="btn btn-primary" type="button" :disabled="saving" @click="save">
              {{ saving ? 'Saving…' : 'Save Changes' }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '../stores/auth.js'

const authStore = useAuthStore()
const { user, isAuthenticated } = storeToRefs(authStore)

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const newInterest = ref('')
const form = reactive({
  track: '',
  profile: {
    firstName: '',
    lastName: '',
    schoolName: '',
    yearLevel: null,
    country: '',
    region: '',
    availability: '',
    bio: '',
    areasOfInterest: []
  }
})

const yearLevelInput = computed({
  get() {
    return form.profile.yearLevel ?? ''
  },
  set(value) {
    if (value === '') {
      form.profile.yearLevel = null
      return
    }
    const parsed = Number(value)
    if (Number.isNaN(parsed)) {
      form.profile.yearLevel = null
    } else {
      form.profile.yearLevel = parsed
    }
  }
})

const displayName = computed(() => user.value?.name || `${form.profile.firstName} ${form.profile.lastName}`.trim())

const getInitials = (name) =>
  (name || '')
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || '—'

const capitalise = (value) => {
  if (!value) return ''
  return value.charAt(0).toUpperCase() + value.slice(1)
}

const applyUserToForm = (u) => {
  if (!u) return
  form.track = u.track || ''
  const profile = u.profile || {}
  form.profile.firstName = profile.firstName || ''
  form.profile.lastName = profile.lastName || ''
  form.profile.schoolName = profile.schoolName || ''
  form.profile.yearLevel = profile.yearLevel ?? null
  form.profile.country = profile.country || ''
  form.profile.region = profile.region || ''
  form.profile.availability = profile.availability || ''
  form.profile.bio = profile.bio || ''
  form.profile.areasOfInterest = Array.isArray(profile.areasOfInterest)
    ? [...profile.areasOfInterest]
    : []
}

watch(user, (val) => {
  applyUserToForm(val)
}, { immediate: true })

onMounted(async () => {
  if (!isAuthenticated.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const latest = await authStore.fetchCurrentUser({ forceRefresh: true })
    applyUserToForm(latest)
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to load profile data'
  } finally {
    loading.value = false
  }
})

const addInterest = () => {
  const value = newInterest.value.trim()
  if (!value) return
  if (!form.profile.areasOfInterest.includes(value)) {
    form.profile.areasOfInterest = [...form.profile.areasOfInterest, value]
  }
  newInterest.value = ''
}

const removeInterest = (target) => {
  form.profile.areasOfInterest = form.profile.areasOfInterest.filter((item) => item !== target)
}

const reset = () => {
  applyUserToForm(user.value)
  newInterest.value = ''
  successMessage.value = ''
  errorMessage.value = ''
}

const save = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  saving.value = true
  try {
    const payload = {
      track: form.track,
      profile: {
        firstName: form.profile.firstName,
        lastName: form.profile.lastName,
        schoolName: form.profile.schoolName,
        yearLevel: form.profile.yearLevel,
        country: form.profile.country,
        region: form.profile.region,
        availability: form.profile.availability,
        bio: form.profile.bio,
        areasOfInterest: form.profile.areasOfInterest
      }
    }
    const updated = await authStore.updateCurrentUser(payload)
    applyUserToForm(updated)
    successMessage.value = 'Profile updated'
  } catch (error) {
    errorMessage.value = error?.message || 'Save failed, please try again later'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.profile-header {
  background: linear-gradient(135deg, var(--dark-green) 0%, #018a63 100%);
  color: var(--white);
  padding: 2.5rem 2rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  text-align: center;
}

.profile-avatar-large {
  width: 104px;
  height: 104px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: var(--white);
  font-size: 2.5rem;
  font-weight: 600;
  display: grid;
  place-items: center;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
}

.profile-name {
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.profile-role {
  font-size: 0.95rem;
  opacity: 0.85;
}

.profile-content {
  padding: 2.25rem 2.5rem;
  background: linear-gradient(180deg, var(--bg-lighter) 0%, var(--white) 100%);
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.profile-section {
  background: var(--white);
  border-radius: var(--radius-lg);
  border: 1.5px solid var(--border-lighter);
  box-shadow: var(--shadow-sm);
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.profile-section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--charcoal);
  margin: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.form-label {
  font-weight: 600;
  font-size: 0.92rem;
  color: var(--charcoal);
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
}

.chip-delete {
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  line-height: 1;
  font-size: 1rem;
  padding: 0;
}

.chip-delete:hover {
  opacity: 0.7;
}

.loading-state {
  padding: 1rem 0;
  color: var(--dark-green);
}

@media (max-width: 768px) {
  .profile-content {
    padding: 1.5rem;
  }

  .profile-section {
    padding: 1.25rem;
  }

  .profile-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}
</style>
