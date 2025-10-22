<template>
  <div class="content-area" v-if="isAdmin">
    <div class="admin-header">
      <h1>Admin Dashboard</h1>
      <div class="admin-header__actions">
        <select
          v-model="activeTrack"
          class="form-control"
          style="width:220px;"
          :disabled="statsLoading || usersLoading"
        >
          <option v-for="option in trackOptions" :key="option" :value="option">
            Track: {{ option }}
          </option>
        </select>
      </div>
    </div>

    <div class="grid grid-4 admin-widgets">
      <button
        type="button"
        class="widget clickable"
        @click="handleCardClick('all')"
      >
        <div class="widget-header">
          <span class="widget-title">Total Users</span>
          <i class="fas fa-users" style="color:var(--eucalypt);"></i>
        </div>
        <div class="widget-value">
          {{ statsLoading ? 'Loading…' : totalUsers }}
        </div>
        <div class="widget-footer">
          <span>Track: {{ activeTrack }}</span>
        </div>
      </button>

      <button
        type="button"
        class="widget clickable"
        @click="focusGroupsSection"
      >
        <div class="widget-header">
          <span class="widget-title">Active Groups</span>
          <i class="fas fa-layer-group" style="color:var(--mint-green);"></i>
        </div>
        <div class="widget-value">
          {{ statsLoading ? 'Loading…' : activeGroups }}
        </div>
        <div class="widget-footer">
          <span>Filtered by track selection</span>
        </div>
      </button>

      <button
        type="button"
        class="widget clickable"
        @click="handleCardClick('mentor')"
      >
        <div class="widget-header">
          <span class="widget-title">Mentors</span>
          <i class="fas fa-user-tie" style="color:var(--air-force-blue);"></i>
        </div>
        <div class="widget-value">
          {{ statsLoading ? 'Loading…' : mentorTotal }}
        </div>
        <div class="widget-footer">
          <span>{{ mentorActive }} active · {{ mentorPending }} pending</span>
        </div>
      </button>

      <button
        type="button"
        class="widget clickable"
        @click="handleCardClick('student')"
      >
        <div class="widget-header">
          <span class="widget-title">Students</span>
          <i class="fas fa-graduation-cap" style="color:var(--yellow);"></i>
        </div>
        <div class="widget-value">
          {{ statsLoading ? 'Loading…' : studentTotal }}
        </div>
        <div class="widget-footer">
          <span>{{ studentPending }} pending (excluded)</span>
        </div>
      </button>
    </div>

    <p v-if="statsErrorMessage" class="admin-error">{{ statsErrorMessage }}</p>

    <div class="data-table">
      <div class="table-header">
        <h3 style="margin:0;">User Management</h3>
        <div class="table-actions">
          <input
            v-model="userSearch"
            type="text"
            class="form-control"
            placeholder="Search users..."
            style="width:250px;"
            :disabled="usersLoading"
          >
          <button class="btn btn-outline" @click="openFilterModal" :disabled="filterOptionsLoading">
            <i class="fas fa-filter"></i> Filter
          </button>
          <button class="btn btn-outline" @click="exportUsers" :disabled="exporting || usersLoading">
            <i class="fas fa-download"></i> Export
          </button>
          <button class="btn btn-primary" @click="openCreateUser" :disabled="creatingUser">
            <i class="fas fa-user-plus"></i> Add User
          </button>
        </div>
      </div>

      <p v-if="usersErrorMessage" class="admin-error">{{ usersErrorMessage }}</p>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  class="table-checkbox"
                  @change="toggleSelectAll($event)"
                  :disabled="usersLoading || !users.length"
                >
              </th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Track</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="usersLoading">
              <td colspan="7" style="text-align:center;color:#6c757d;">Loading users…</td>
            </tr>
            <template v-else>
              <tr v-if="!users.length">
                <td colspan="7" style="text-align:center;color:#6c757d;">No users found</td>
              </tr>
              <tr v-else v-for="user in users" :key="user.id">
                <td>
                  <input
                    type="checkbox"
                    class="table-checkbox"
                    v-model="selected"
                    :value="user.id"
                  >
                </td>
                <td>{{ user.name }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.role }}</td>
                <td>{{ user.track || '—' }}</td>
                <td>
                  <span
                    :class="[
                      'status-badge',
                      user.status === 'active'
                        ? 'status-active'
                        : user.status === 'pending'
                          ? 'status-pending'
                          : 'status-inactive'
                    ]"
                  >
                    {{ user.status }}
                  </span>
                </td>
                <td>
                  <div class="user-actions">
                    <select
                      :value="user.status"
                      class="form-control"
                      style="width:130px;"
                      @change="onChangeStatus(user.id, $event.target.value)"
                      :disabled="Boolean(updatingStatus[user.id])"
                    >
                      <option v-for="option in statusOptions" :key="option" :value="option">
                        {{ option.charAt(0).toUpperCase() + option.slice(1) }}
                      </option>
                    </select>
                    <button
                      class="btn btn-outline btn-sm"
                      @click="openEditUser(user.id)"
                      :disabled="Boolean(savingUser[user.id])"
                    >
                      Edit
                    </button>
                    <button
                      class="btn btn-outline btn-sm"
                      @click="openViewUser(user.id)"
                    >
                      View
                    </button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Filter Panel -->
    <div v-if="showFilterModal" class="panel-overlay" @click.self="closeFilterModal">
      <aside class="panel panel--filter">
        <header class="panel__header">
          <div>
            <h3>Filter Users</h3>
            <p class="panel__subtitle">Filter users by role and status</p>
          </div>
          <button class="btn btn-ghost" @click="closeFilterModal" aria-label="Close filter panel">
            <i class="fas fa-times"></i>
          </button>
        </header>

        <section class="panel__body">
          <div class="panel__form">
            <label class="form-field">
              <span>Role</span>
              <select v-model="filterForm.role" class="form-control">
                <option value="">All Roles</option>
                <option v-for="role in roleOptions" :key="role" :value="role">
                  {{ role.charAt(0).toUpperCase() + role.slice(1) }}
                </option>
              </select>
            </label>
            <label class="form-field">
              <span>Status</span>
              <select v-model="filterForm.status" class="form-control">
                <option value="">All Statuses</option>
                <option v-for="status in statusOptions" :key="status" :value="status">
                  {{ status.charAt(0).toUpperCase() + status.slice(1) }}
                </option>
              </select>
            </label>
          </div>
        </section>

        <footer class="panel__footer">
          <button class="btn btn-outline" @click="clearFilters">Reset</button>
          <button class="btn btn-primary" @click="applyFilters">Apply</button>
        </footer>
      </aside>
    </div>

    <!-- User Side Panel -->
    <div v-if="showUserModal" class="panel-overlay" @click.self="closeUserModal">
      <aside class="panel" :class="`panel--${userModalMode}`">
        <header class="panel__header">
          <div>
            <h3>{{ userModalTitle }}</h3>
            <p class="panel__subtitle" v-if="userModalMode === 'view'">
              View user profile information
            </p>
            <p class="panel__subtitle" v-else-if="userModalMode === 'edit'">
              Update user details and profile
            </p>
            <p class="panel__subtitle" v-else>
              Create a new user and add them to the platform
            </p>
          </div>
          <button class="btn btn-ghost" @click="closeUserModal" aria-label="Close user panel">
            <i class="fas fa-times"></i>
          </button>
        </header>

        <section class="panel__body">
          <div v-if="userModalLoading" class="panel__loading">
            Loading user information…
          </div>
          <div v-else class="panel__form">
            <div class="form-grid">
              <label class="form-field">
                <span>Email</span>
                <input
                  v-model="userForm.email"
                  type="email"
                  class="form-control"
                  :readonly="userModalMode === 'view'"
                  :disabled="isSavingUser"
                >
              </label>
              <label class="form-field">
                <span>Role</span>
                <select
                  v-model="userForm.role"
                  class="form-control"
                  :disabled="userModalMode === 'view' || isSavingUser"
                >
                  <option v-for="role in roleOptions" :key="role" :value="role">
                    {{ role.charAt(0).toUpperCase() + role.slice(1) }}
                  </option>
                </select>
              </label>
              <label class="form-field">
                <span>Status</span>
                <select
                  v-model="userForm.status"
                  class="form-control"
                  :disabled="userModalMode === 'view' || isSavingUser"
                >
                  <option v-for="status in statusOptions" :key="status" :value="status">
                    {{ status.charAt(0).toUpperCase() + status.slice(1) }}
                  </option>
                </select>
              </label>
              <label class="form-field">
                <span>Track</span>
                <select
                  v-model="userForm.track"
                  class="form-control"
                  :disabled="userModalMode === 'view' || isSavingUser"
                >
                  <option v-for="option in trackOptions" :key="`${option}-form`" :value="option">
                    {{ option }}
                  </option>
                </select>
              </label>
              <label class="form-field">
                <span>First Name</span>
                <input
                  v-model="userForm.profile.firstName"
                  type="text"
                  class="form-control"
                  :readonly="userModalMode === 'view'"
                  :disabled="isSavingUser"
                >
              </label>
              <label class="form-field">
                <span>Last Name</span>
                <input
                  v-model="userForm.profile.lastName"
                  type="text"
                  class="form-control"
                  :readonly="userModalMode === 'view'"
                  :disabled="isSavingUser"
                >
              </label>
              <label class="form-field">
                <span>School</span>
                <input
                  v-model="userForm.profile.schoolName"
                  type="text"
                  class="form-control"
                  :readonly="userModalMode === 'view'"
                  :disabled="isSavingUser"
                >
              </label>
              <label class="form-field">
                <span>Year Level</span>
                <input
                  v-model="userForm.profile.yearLevel"
                  type="number"
                  min="0"
                  class="form-control"
                  :readonly="userModalMode === 'view'"
                  :disabled="isSavingUser"
                >
              </label>
              <label class="form-field">
                <span>Country</span>
                <input
                  v-model="userForm.profile.country"
                  type="text"
                  class="form-control"
                  :readonly="userModalMode === 'view'"
                  :disabled="isSavingUser"
                >
              </label>
              <label class="form-field">
                <span>Region</span>
                <input
                  v-model="userForm.profile.region"
                  type="text"
                  class="form-control"
                  :readonly="userModalMode === 'view'"
                  :disabled="isSavingUser"
                >
              </label>
            </div>

            <label class="form-field">
              <span>Areas of Interest (comma or newline separated)</span>
              <textarea
                v-model="userForm.profile.areasOfInterestText"
                class="form-control"
                rows="3"
                :readonly="userModalMode === 'view'"
                :disabled="isSavingUser"
              ></textarea>
            </label>
            <label class="form-field">
              <span>Availability</span>
              <textarea
                v-model="userForm.profile.availability"
                class="form-control"
                rows="2"
                :readonly="userModalMode === 'view'"
                :disabled="isSavingUser"
              ></textarea>
            </label>
            <label class="form-field">
              <span>Bio</span>
              <textarea
                v-model="userForm.profile.bio"
                class="form-control"
                rows="3"
                :readonly="userModalMode === 'view'"
                :disabled="isSavingUser"
              ></textarea>
            </label>
          </div>
        </section>

        <footer class="panel__footer">
          <button
            v-if="userModalMode === 'edit'"
            class="btn btn-danger btn-spacer"
            @click="confirmDeleteUser"
            :disabled="isDeletingUser"
          >
            Delete
          </button>
          <button class="btn btn-outline" @click="closeUserModal" :disabled="isSavingUser || isDeletingUser">Close</button>
          <button
            v-if="userModalMode !== 'view'"
            class="btn btn-primary"
            @click="saveUser"
            :disabled="isSavingUser || isDeletingUser"
          >
            {{ userModalMode === 'create' ? 'Create' : 'Save' }}
          </button>
        </footer>
      </aside>
    </div>

    <!-- Groups Panel -->
    <div v-if="showGroups" class="panel-overlay" @click.self="closeGroupsModal">
      <aside class="panel">
        <header class="panel__header">
          <div>
            <h3>Active Groups ({{ activeTrack }})</h3>
            <p class="panel__subtitle">Create a new group or review existing ones.</p>
          </div>
          <button class="btn btn-ghost" @click="closeGroupsModal" aria-label="Close groups panel">
            <i class="fas fa-times"></i>
          </button>
        </header>

        <section class="panel__body">
          <div v-if="groupsLoading && !groups.length" class="panel__loading">
            Loading groups…
          </div>
          <div>
            <div class="group-create">
              <h4>Create New Group</h4>
              <div class="group-create__form">
                <label class="form-field">
                  <span>Group Code (optional)</span>
                  <input
                    v-model="groupForm.groupId"
                    type="text"
                    class="form-control"
                    :disabled="creatingGroup"
                    placeholder="e.g. BTF046"
                  >
                </label>
                <label class="form-field">
                  <span>Name</span>
                  <input
                    v-model="groupForm.name"
                    type="text"
                    class="form-control"
                    :disabled="creatingGroup"
                    placeholder="Team name"
                    required
                  >
                </label>
                <label class="form-field">
                  <span>Track</span>
                  <input
                    v-model="groupForm.track"
                    type="text"
                    class="form-control"
                    :disabled="creatingGroup"
                  >
                </label>
                <label class="form-field">
                  <span>Mentor</span>
                  <select
                    v-model="groupForm.mentorId"
                    class="form-control"
                    :disabled="creatingGroup || loadingGroupOptions"
                  >
                    <option value="">No mentor</option>
                    <option v-for="mentor in availableMentors" :key="mentor.id" :value="String(mentor.id)">
                      {{ mentor.name }}
                    </option>
                  </select>
                </label>
                <label class="form-field form-field--full">
                  <span>Members</span>
                  <select
                    v-model="groupForm.memberIds"
                    multiple
                    class="form-control group-create__members"
                    :disabled="creatingGroup || loadingGroupOptions"
                  >
                    <option v-for="member in availableMembers" :key="member.id" :value="String(member.id)">
                      {{ member.name }}
                    </option>
                  </select>
                  <small>Select at least one member. Hold Cmd/Ctrl to pick multiple.</small>
                </label>
              </div>
              <div class="group-create__actions">
                <button
                  class="btn btn-primary"
                  @click="createGroup"
                  :disabled="creatingGroup || loadingGroupOptions || !groupForm.name.trim() || groupForm.memberIds.length === 0"
                >
                  {{ creatingGroup ? 'Creating…' : 'Create Group' }}
                </button>
              </div>
              <p v-if="loadingGroupOptions" class="admin-empty">Loading available mentors and members…</p>
            </div>

            <hr>

            <p v-if="groupsError" class="admin-error">{{ groupsError }}</p>
            <ul v-if="groups.length" class="group-list">
              <li v-for="group in groups" :key="group.id" class="group-item">
                <div class="group-title">{{ group.name }}</div>
                <div class="group-meta">
                  Track: {{ group.track || '—' }} · Members: {{ group.members }}
                </div>
                <div class="group-meta">
                  Mentor: {{ group.mentor?.name || '—' }}
                </div>
                <div class="group-actions">
                  <button
                    class="btn btn-danger btn-sm"
                    @click="deleteGroup(group.id)"
                    :disabled="Boolean(deletingGroups[group.id])"
                  >
                    {{ deletingGroups[group.id] ? 'Deleting…' : 'Delete' }}
                  </button>
                </div>
              </li>
            </ul>
            <p v-else-if="!groupsLoading" class="admin-empty">No active groups found for this track.</p>
          </div>
        </section>

        <footer class="panel__footer">
          <button class="btn btn-primary" @click="closeGroupsModal">Close</button>
        </footer>
      </aside>
    </div>
  </div>

  <div class="content-area" v-else>
    <h1>Admin Dashboard</h1>
    <p style="margin-top:1rem;">This area is only available to administrators.</p>
  </div>
</template>

<script setup>
import {
  ref,
  reactive,
  computed,
  watch,
  onBeforeUnmount,
  onMounted
} from 'vue'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'
import { safeJson } from '@/utils/http'

const authStore = useAuthStore()
const adminStore = useAdminStore()

const {
  stats,
  statsLoading,
  statsError,
  users,
  usersLoading,
  usersError,
  updatingStatus,
  filterOptions,
  filterOptionsLoading,
  filterOptionsError,
  creatingUser,
  savingUser,
  detailLoading,
  exporting,
  deletingUser
} = storeToRefs(adminStore)

const { isAdmin } = storeToRefs(authStore)

const userSearch = ref(adminStore.filters.search || '')
const filterForm = reactive({
  role: adminStore.filters.role || '',
  status: adminStore.filters.status || ''
})
const selected = ref([])

const activeTrack = ref(adminStore.filters.track || 'Global')
const showFilterModal = ref(false)
const showUserModal = ref(false)
const showGroups = ref(false)

const userModalMode = ref('view') // view | edit | create
const userModalLoading = ref(false)

const userForm = reactive({
  id: null,
  email: '',
  role: 'student',
  track: 'Global',
  status: 'pending',
  profile: {
    firstName: '',
    lastName: '',
    schoolName: '',
    yearLevel: '',
    country: '',
    region: '',
    areasOfInterestText: '',
    availability: '',
    bio: ''
  }
})

const groups = ref([])
const groupsLoaded = ref(false)
const groupsLoading = ref(false)
const groupsError = ref('')
const deletingGroups = ref({})
const loadingGroupOptions = ref(false)
const groupOptionsLoaded = ref(false)
const creatingGroup = ref(false)
const availableMentors = ref([])
const availableMembers = ref([])
const groupForm = reactive({
  groupId: '',
  name: '',
  track: activeTrack.value || 'Global',
  mentorId: '',
  memberIds: []
})

const statusOptions = computed(() => filterOptions.value.statuses || ['active', 'pending', 'inactive'])
const roleOptions = computed(() => filterOptions.value.roles || ['student', 'mentor', 'supervisor', 'admin'])

const trackOptions = computed(() => {
  const base = filterOptions.value.tracks?.length ? filterOptions.value.tracks : ['Global', 'AUS-NSW', 'Brazil']
  const normalized = base.map((item) => (item && item.toLowerCase() !== 'global' ? item : 'Global'))
  const unique = []
  for (const item of ['Global', ...normalized]) {
    if (!unique.includes(item)) unique.push(item)
  }
  return unique
})

const totalUsers = computed(() => stats.value?.totalUsers ?? 0)
const activeGroups = computed(() => stats.value?.activeGroups ?? 0)
const mentorTotal = computed(() => stats.value?.mentors?.total ?? 0)
const mentorActive = computed(() => stats.value?.mentors?.active ?? 0)
const mentorPending = computed(() => stats.value?.mentors?.pending ?? 0)
const studentTotal = computed(() => stats.value?.students?.total ?? 0)
const studentPending = computed(() => stats.value?.students?.pending ?? 0)

const statsErrorMessage = computed(() => statsError.value?.message ?? '')
const usersErrorMessage = computed(() => usersError.value?.message ?? filterOptionsError.value?.message ?? '')

const userModalTitle = computed(() => {
  if (userModalMode.value === 'create') return 'Add User'
  if (userModalMode.value === 'edit') return 'Edit User'
  return 'View User'
})

const isSavingUser = computed(() => {
  if (userModalMode.value === 'create') return creatingUser.value
  if (userForm.id != null) {
    return Boolean(savingUser.value[userForm.id])
  }
  return false
})

const isDeletingUser = computed(() =>
  userForm.id != null ? Boolean(deletingUser.value?.[userForm.id]) : false
)

const focusGroupsSection = () => {
  openGroupsModal()
}

const refreshForTrack = (track) => {
  adminStore.fetchStats({ track }).catch(() => {})
  adminStore.fetchUsers({
    track,
    search: userSearch.value,
    role: filterForm.role,
    status: filterForm.status
  }).catch(() => {})
}

watch(
  isAdmin,
  (value) => {
    if (value) {
      refreshForTrack(activeTrack.value)
      if (showGroups.value) {
        groupsLoaded.value = false
        groupOptionsLoaded.value = false
        fetchGroups(true).catch(() => {})
        loadGroupOptions(true).catch(() => {})
      }
    } else {
      adminStore.reset()
      groups.value = []
      groupsLoaded.value = false
      availableMentors.value = []
      availableMembers.value = []
      groupOptionsLoaded.value = false
      resetGroupForm()
    }
  },
  { immediate: true }
)

watch(
  () => adminStore.filters.track,
  (value) => {
    if (value && value !== activeTrack.value) {
      activeTrack.value = value
    }
  }
)

watch(
  () => adminStore.filters.role,
  (value) => {
    if (value !== filterForm.role) filterForm.role = value || ''
  }
)

watch(
  () => adminStore.filters.status,
  (value) => {
    if (value !== filterForm.status) filterForm.status = value || ''
  }
)

watch(
  () => adminStore.filters.search,
  (value) => {
    if ((value || '') !== userSearch.value) {
      userSearch.value = value || ''
    }
  }
)

watch(showGroups, (visible) => {
  if (visible) {
    groupsLoaded.value = false
    groupOptionsLoaded.value = false
    fetchGroups(true).catch(() => {})
    loadGroupOptions(true).catch(() => {})
  }
})

watch(activeTrack, (track, previous) => {
  if (!isAdmin.value || track === previous) return
  refreshForTrack(track)
  if (userModalMode.value === 'create' && showUserModal.value) {
    userForm.track = track
  }
  groupForm.track = track || 'Global'
  if (showGroups.value) {
    groupsLoaded.value = false
    groupOptionsLoaded.value = false
    fetchGroups(true).catch(() => {})
    loadGroupOptions(true).catch(() => {})
  }
})

let searchDebounceHandle = null
watch(userSearch, (value, previous) => {
  if (!isAdmin.value) return
  if (value === previous) return
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
  searchDebounceHandle = setTimeout(() => {
    adminStore.fetchUsers({
      track: activeTrack.value,
      search: value,
      role: filterForm.role,
      status: filterForm.status
    }).catch(() => {})
  }, 300)
})

onBeforeUnmount(() => {
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
})

onMounted(() => {
  adminStore.fetchFilterOptions().catch(() => {})
})

const toggleSelectAll = (event) => {
  if (event.target.checked) {
    selected.value = users.value.map((user) => user.id)
  } else {
    selected.value = []
  }
}

const onChangeStatus = async (userId, nextStatus) => {
  if (!isAdmin.value) return
  const current = users.value.find((user) => user.id === userId)?.status
  if (!nextStatus || nextStatus === current) return

  try {
    await adminStore.updateUserStatus({ userId, status: nextStatus })
  } catch (error) {
    window.alert(error?.message || 'Failed to update user status.')
  }
}

const openFilterModal = async () => {
  try {
    await adminStore.fetchFilterOptions()
  } catch (error) {
    window.alert(error?.message || 'Failed to load filter options')
    return
  }
  filterForm.role = adminStore.filters.role || ''
  filterForm.status = adminStore.filters.status || ''
  showFilterModal.value = true
}

const closeFilterModal = () => {
  showFilterModal.value = false
}

const applyFilters = async () => {
  try {
    await adminStore.fetchUsers({
      track: activeTrack.value,
      role: filterForm.role,
      status: filterForm.status,
      search: userSearch.value
    })
    showFilterModal.value = false
  } catch (error) {
    window.alert(error?.message || 'Failed to apply filters')
  }
}

const clearFilters = () => {
  filterForm.role = ''
  filterForm.status = ''
  userSearch.value = ''
  applyFilters()
}

const openCreateUser = async () => {
  userModalMode.value = 'create'
  const ready = await ensureFilterOptions()
  if (!ready) return
  resetUserForm()
  showUserModal.value = true
}

const openEditUser = async (userId) => {
  userModalMode.value = 'edit'
  const ready = await ensureFilterOptions()
  if (!ready) return
  await openUserDetail(userId)
}

const openViewUser = async (userId) => {
  userModalMode.value = 'view'
  const ready = await ensureFilterOptions()
  if (!ready) return
  await openUserDetail(userId)
}

const openUserDetail = async (userId) => {
  userModalLoading.value = true
  showUserModal.value = true
  try {
    const detail = await adminStore.fetchUserDetail(userId, { forceRefresh: true })
    populateUserForm(detail)
  } catch (error) {
    window.alert(error?.message || 'Failed to load user information')
    showUserModal.value = false
  } finally {
    userModalLoading.value = false
  }
}

const closeUserModal = () => {
  showUserModal.value = false
}

const ensureFilterOptions = async () => {
  try {
    await adminStore.fetchFilterOptions({ forceRefresh: !adminStore.filterOptions.tracks.length })
    return true
  } catch (error) {
    window.alert(error?.message || 'Failed to load filter options. Please try again later.')
    return false
  }
}

const resetUserForm = () => {
  userForm.id = null
  userForm.email = ''
  userForm.role = 'student'
  userForm.track = activeTrack.value || 'Global'
  userForm.status = 'pending'
  Object.assign(userForm.profile, {
    firstName: '',
    lastName: '',
    schoolName: '',
    yearLevel: '',
    country: '',
    region: '',
    areasOfInterestText: '',
    availability: '',
    bio: ''
  })
}

const resetGroupForm = () => {
  groupForm.groupId = ''
  groupForm.name = ''
  groupForm.track = activeTrack.value || 'Global'
  groupForm.mentorId = ''
  groupForm.memberIds = []
}

const populateUserForm = (detail) => {
  resetUserForm()
  userForm.id = detail?.id ?? null
  userForm.email = detail?.email || ''
  userForm.role = detail?.role || 'student'
  userForm.track = detail?.track ? detail.track : 'Global'
  userForm.status = detail?.status || 'pending'

  const profile = detail?.profile || {}
  userForm.profile.firstName = profile.firstName || ''
  userForm.profile.lastName = profile.lastName || ''
  userForm.profile.schoolName = profile.schoolName || ''
  userForm.profile.yearLevel = profile.yearLevel != null ? String(profile.yearLevel) : ''
  userForm.profile.country = profile.country || ''
  userForm.profile.region = profile.region || ''
  userForm.profile.areasOfInterestText = Array.isArray(profile.areasOfInterest)
    ? profile.areasOfInterest.join(', ')
    : ''
  userForm.profile.availability = profile.availability || ''
  userForm.profile.bio = profile.bio || ''
}

const buildUserPayload = () => {
  const email = String(userForm.email || '').trim().toLowerCase()
  if (!email) {
    throw new Error('Email is required')
  }

  const payload = {
    email,
    role: userForm.role,
    status: userForm.status,
    track: userForm.track && userForm.track.toLowerCase() !== 'global' ? userForm.track : ''
  }

  const profilePayload = {}
  const pushProfile = (key, value) => {
    if (typeof value === 'string') {
      const trimmed = value.trim()
      if (trimmed || userModalMode.value === 'edit') {
        profilePayload[key] = trimmed
      }
      return
    }
    if (value != null) {
      profilePayload[key] = value
    } else if (userModalMode.value === 'edit') {
      profilePayload[key] = null
    }
  }

  pushProfile('firstName', userForm.profile.firstName)
  pushProfile('lastName', userForm.profile.lastName)
  pushProfile('schoolName', userForm.profile.schoolName)
  pushProfile('country', userForm.profile.country)
  pushProfile('region', userForm.profile.region)
  pushProfile('availability', userForm.profile.availability)
  pushProfile('bio', userForm.profile.bio)

  if (userForm.profile.yearLevel !== '') {
    const parsed = parseInt(userForm.profile.yearLevel, 10)
    if (!Number.isNaN(parsed)) {
      profilePayload.yearLevel = parsed
    } else if (userModalMode.value === 'edit') {
      profilePayload.yearLevel = null
    }
  } else if (userModalMode.value === 'edit') {
    profilePayload.yearLevel = null
  }

  const interests = userForm.profile.areasOfInterestText
    .split(/[,\\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
  if (interests.length) {
    profilePayload.areasOfInterest = interests
  } else if (userModalMode.value === 'edit') {
    profilePayload.areasOfInterest = []
  }

  if (Object.keys(profilePayload).length) {
    payload.profile = profilePayload
  }

  return payload
}

const saveUser = async () => {
  try {
    const payload = buildUserPayload()
    if (userModalMode.value === 'create') {
      await adminStore.createUser(payload)
    } else if (userModalMode.value === 'edit' && userForm.id != null) {
      await adminStore.updateUser(userForm.id, payload)
    }
    showUserModal.value = false
  } catch (error) {
    window.alert(error?.message || 'Failed to save changes')
  }
}

const confirmDeleteUser = async () => {
  if (userModalMode.value !== 'edit' || userForm.id == null) return
  const confirmed = window.confirm('Delete this user? This action cannot be undone.')
  if (!confirmed) return

  try {
    await adminStore.deleteUser(userForm.id)
    showUserModal.value = false
  } catch (error) {
    window.alert(error?.message || 'Failed to delete user')
  }
}

const handleCardClick = (type) => {
  if (type === 'mentor') {
    filterForm.role = 'mentor'
    filterForm.status = ''
  } else if (type === 'student') {
    filterForm.role = 'student'
    filterForm.status = ''
  } else {
    filterForm.role = ''
    filterForm.status = ''
  }
  userSearch.value = ''
  applyFilters()
  if (type === 'all') {
    nextTick(() => {
      document.querySelector('.data-table')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }
}

const openGroupsModal = async () => {
  if (!isAdmin.value) return
  showGroups.value = true
  if (!groupsLoaded.value) {
    await fetchGroups(true).catch(() => {})
  }
  if (!groupOptionsLoaded.value) {
    await loadGroupOptions(true).catch(() => {})
  }
}

const closeGroupsModal = () => {
  showGroups.value = false
}

const fetchGroups = async (force = false) => {
  if (!isAdmin.value) return []
  if (groupsLoading.value) return groups.value
  if (groupsLoaded.value && !force) return groups.value

  groupsLoading.value = true
  groupsError.value = ''

  try {
    const params = new URLSearchParams()
    params.append('status', 'active')
    if (activeTrack.value && activeTrack.value.toLowerCase() !== 'global') {
      params.append('track', activeTrack.value)
    }

    const response = await authStore.authenticatedFetch(
      `/groups/${params.toString() ? `?${params.toString()}` : ''}`
    )
    const data = await safeJson(response)
    if (!response.ok) {
      throw new Error(data?.error || 'Failed to load groups')
    }

    groups.value = Array.isArray(data?.groups) ? data.groups : []
    groupsLoaded.value = true
    return groups.value
  } catch (error) {
    groupsError.value = error?.message || 'Failed to fetch groups'
    throw error
  } finally {
    groupsLoading.value = false
  }
}

const loadGroupOptions = async (force = false) => {
  if (!isAdmin.value) return
  if (loadingGroupOptions.value) return
  if (groupOptionsLoaded.value && !force) return

  loadingGroupOptions.value = true

  const fetchUserOptions = async (query) => {
    const response = await authStore.authenticatedFetch(`/admin/users/${query}`)
    const data = await safeJson(response)
    if (!response.ok) {
      throw new Error(data?.error || 'Failed to load user options')
    }

    const results = Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data)
        ? data
        : []

    return results.map((item) => ({
      id: item.id,
      name: item.name || item.email
    }))
  }

  const trackValue = (activeTrack.value || '').trim()
  const trackQuery =
    trackValue && trackValue.toLowerCase() !== 'global'
      ? `&track=${encodeURIComponent(trackValue)}`
      : ''

  try {
    availableMentors.value = await fetchUserOptions(`?status=active&role=mentor${trackQuery}&page_size=200`)
    availableMembers.value = await fetchUserOptions(`?status=active&role=student${trackQuery}&page_size=500`)
    groupOptionsLoaded.value = true
  } catch (error) {
    window.alert(error?.message || 'Failed to load user options')
  } finally {
    loadingGroupOptions.value = false
  }
}

const createGroup = async () => {
  const name = groupForm.name.trim()
  if (!name) {
    window.alert('Group name is required')
    return
  }

  if (!groupForm.memberIds.length) {
    window.alert('Please select at least one member')
    return
  }

  creatingGroup.value = true

  let mentorId =
    groupForm.mentorId === null || groupForm.mentorId === ''
      ? null
      : Number(groupForm.mentorId)

  if (mentorId !== null && !Number.isFinite(mentorId)) {
    mentorId = null
  }

  const memberIds = Array.from(
    new Set(
      groupForm.memberIds
        .map((id) => Number(id))
        .filter((id) => Number.isFinite(id))
    )
  )

  const payload = {
    groupId: groupForm.groupId.trim() || null,
    name,
    track:
      (groupForm.track || '').trim().toLowerCase() === 'global'
        ? ''
        : (groupForm.track || '').trim(),
    mentorId,
    members: memberIds.map((id) => ({ userId: id, role: 'student' }))
  }

  try {
    const response = await authStore.authenticatedFetch('/groups/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    const data = await safeJson(response)
    if (!response.ok) {
      throw new Error(data?.error || 'Failed to create group')
    }

    await fetchGroups(true)
    await adminStore.fetchStats({ track: activeTrack.value })
    resetGroupForm()
    await loadGroupOptions(true)
    window.alert('Group created successfully')
  } catch (error) {
    window.alert(error?.message || 'Failed to create group')
  } finally {
    creatingGroup.value = false
  }
}

const deleteGroup = async (groupId) => {
  if (!groupId) return
  const confirmed = window.confirm('Delete this group? This action cannot be undone.')
  if (!confirmed) return

  deletingGroups.value = { ...deletingGroups.value, [groupId]: true }

  try {
    const response = await authStore.authenticatedFetch(`/groups/${groupId}/`, {
      method: 'DELETE'
    })

    if (!response.ok && response.status !== 204) {
      const data = await safeJson(response)
      throw new Error(data?.error || 'Failed to delete group')
    }

    await adminStore.fetchStats({ track: activeTrack.value })
    await fetchGroups(true)
  } catch (error) {
    window.alert(error?.message || 'Failed to delete group')
  } finally {
    const { [groupId]: _discard, ...rest } = deletingGroups.value
    deletingGroups.value = rest
  }
}

const exportUsers = async () => {
  try {
    const { blob, filename } = await adminStore.exportUsers()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    window.alert(error?.message || 'Failed to export data')
  }
}
</script>

<style scoped>
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.admin-header__actions {
  display: flex;
  gap: 1rem;
}

.admin-widgets {
  margin-bottom: 2rem;
}

.admin-error {
  color: #d9534f;
  margin: 0 0 1rem;
}

.admin-empty {
  color: #6c757d;
  margin: 1rem 0;
}

.widget.clickable {
  cursor: pointer;
  border: none;
  text-align: left;
  background: #fff;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.widget.clickable:focus,
.widget.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.widget.clickable:disabled {
  cursor: default;
  transform: none;
  box-shadow: none;
}

.data-table .user-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-field span {
  font-size: 0.9rem;
  color: #495057;
}

.form-field--full {
  grid-column: 1 / -1;
}

.btn-ghost {
  background: transparent;
  border: none;
  color: #6c757d;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
}

.btn-ghost:hover {
  color: #212529;
}

.group-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.group-item {
  border: 1px solid #e3e6ea;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.group-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #1a3d2f;
}

.group-meta {
  font-size: 0.9rem;
  color: #495057;
}

.panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  justify-content: flex-end;
  align-items: stretch;
  z-index: 1100;
}

.panel {
  width: min(520px, 100%);
  background: #fff;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.18);
  animation: slideIn 0.25s ease;
}

.panel__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  border-bottom: 1px solid #e3e6ea;
  gap: 1rem;
}

.panel__header h3 {
  margin: 0 0 0.25rem;
}

.panel__subtitle {
  margin: 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.panel__body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.panel__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 16px 24px;
  border-top: 1px solid #e3e6ea;
}

.panel--filter {
  width: min(360px, 100%);
}

.panel--create {
  width: min(520px, 100%);
}

.panel--edit {
  width: min(520px, 100%);
}

.panel--view {
  width: min(520px, 100%);
}

.panel__loading {
  text-align: center;
  color: #6c757d;
  padding: 2rem 0;
}

.panel__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.btn-danger {
  border-color: #d9534f;
  color: #d9534f;
}

.btn-danger:hover:not(:disabled) {
  background: #d9534f;
  color: #fff;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spacer {
  margin-right: auto;
}

.group-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}


.group-create {
  margin-bottom: 1.5rem;
}

.group-create h4 {
  margin: 0 0 0.5rem;
}

.group-create__form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.group-create__members {
  min-height: 140px;
}

.group-create__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}


@keyframes slideIn {
  from {
    transform: translateX(30px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
