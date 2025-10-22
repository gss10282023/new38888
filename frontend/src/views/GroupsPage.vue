<template>
  <div class="content-area groups-page">
    <div class="page-header">
      <h2>Active Groups</h2>
      <div class="header-actions">
        <button
          class="btn btn-outline btn-sm"
          type="button"
          :disabled="loading"
          @click="loadGroups(true)"
        >
          <i class="fas fa-sync-alt"></i>
          Refresh
        </button>
      </div>
    </div>

    <div v-if="!isAdmin" class="alert-warning">
      Only administrators can view the full group list.
    </div>

    <div v-else class="card">
      <div class="card-header">
        <h3 class="card-title">All Active Groups</h3>
        <span v-if="groups.length" class="muted">{{ groups.length }} total</span>
      </div>
      <div class="card-content">
        <div v-if="loading" class="empty-state">Loading groups…</div>
        <div v-else-if="errorMessage" class="alert-error">{{ errorMessage }}</div>
        <div v-else-if="!groups.length" class="empty-state">No groups found.</div>
        <div v-else class="groups-table-wrapper">
          <table class="groups-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Mentor</th>
                <th>Members</th>
                <th>Status</th>
                <th>Track</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="group in groups"
                :key="group.id"
                @click="openGroup(group.id)"
              >
                <td>{{ group.id }}</td>
                <td>{{ group.name }}</td>
                <td>{{ group.mentor?.name || '—' }}</td>
                <td>{{ group.members ?? '—' }}</td>
                <td>
                  <span class="status-pill">{{ group.status || '—' }}</span>
                </td>
                <td>{{ group.track || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useGroupStore } from '@/stores/groups'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const groupStore = useGroupStore()
const authStore = useAuthStore()

const { allGroups, loadingAllGroups, errorAllGroups } = storeToRefs(groupStore)
const { isAdmin } = storeToRefs(authStore)

const loading = computed(() => loadingAllGroups.value)
const errorMessage = computed(() => errorAllGroups.value?.message || '')
const groups = computed(() => allGroups.value || [])

const loadGroups = async (force = false) => {
  if (!isAdmin.value) return
  try {
    await groupStore.fetchAllGroups({ forceRefresh: force })
  } catch (error) {
    console.error('Failed to load groups', error)
  }
}

const openGroup = (groupId) => {
  router.push(`/groups/${groupId}`)
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.groups-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.groups-table-wrapper {
  overflow-x: auto;
}

.groups-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.groups-table thead {
  background-color: #f5f7f9;
  text-align: left;
}

.groups-table th,
.groups-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-light);
}

.groups-table tbody tr {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.groups-table tbody tr:hover {
  background-color: #f0f6f4;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background-color: var(--light-green);
  color: var(--dark-green);
  font-size: 0.8rem;
  font-weight: 600;
}

.muted {
  color: #6c757d;
  font-size: 0.9rem;
}

.alert-warning {
  padding: 1rem;
  border: 1px solid #fcd27d;
  background-color: #fff3cd;
  color: #8d6b1a;
  border-radius: 8px;
}

.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #6c757d;
}
</style>
