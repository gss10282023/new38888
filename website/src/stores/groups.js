import { defineStore } from 'pinia'
import { safeJson } from '@/utils/http'
import { useAuthStore } from '@/stores/auth'

export const useGroupStore = defineStore('groups', {
  state: () => ({
    myGroups: [],
    myGroupsLoaded: false,
    loadingMyGroups: false,
    allGroups: [],
    allGroupsLoaded: false,
    loadingAllGroups: false,
    loadingById: {},
    groupsById: {},
    errorMyGroups: null,
    errorAllGroups: null,
    errorById: {}
  }),
  actions: {
    reset() {
      this.myGroups = []
      this.myGroupsLoaded = false
      this.loadingMyGroups = false
      this.allGroups = []
      this.allGroupsLoaded = false
      this.loadingAllGroups = false
      this.loadingById = {}
      this.groupsById = {}
      this.errorMyGroups = null
      this.errorAllGroups = null
      this.errorById = {}
    },

    async fetchMyGroups({ forceRefresh = false } = {}) {
      if (this.loadingMyGroups) return this.myGroups
      if (this.myGroupsLoaded && !forceRefresh) return this.myGroups

      this.loadingMyGroups = true
      this.errorMyGroups = null

      try {
        const auth = useAuthStore()
        const response = await auth.authenticatedFetch('/groups/my-groups/')
        const data = await safeJson(response)
        if (!response.ok) {
          throw new Error(data?.error || '无法获取群组列表')
        }

        this.myGroups = Array.isArray(data?.groups) ? data.groups : []
        this.myGroupsLoaded = true

        this.myGroups.forEach((group) => {
          const existing = this.groupsById[group.id]
          this.groupsById[group.id] = existing
            ? { ...existing, ...group }
            : { ...group }
        })

        return this.myGroups
      } catch (error) {
        this.errorMyGroups = error
        throw error
      } finally {
        this.loadingMyGroups = false
      }
    },

    async fetchAllGroups({ forceRefresh = false } = {}) {
      if (this.loadingAllGroups) return this.allGroups
      if (this.allGroupsLoaded && !forceRefresh) return this.allGroups

      this.loadingAllGroups = true
      this.errorAllGroups = null

      try {
        const auth = useAuthStore()
        const response = await auth.authenticatedFetch('/groups/')
        const data = await safeJson(response)
        if (!response.ok) {
          throw new Error(data?.error || '无法获取全部群组')
        }

        this.allGroups = Array.isArray(data?.groups) ? data.groups : []
        this.allGroupsLoaded = true

        this.allGroups.forEach((group) => {
          const existing = this.groupsById[group.id]
          this.groupsById[group.id] = existing
            ? { ...existing, ...group }
            : { ...group }
        })

        return this.allGroups
      } catch (error) {
        this.errorAllGroups = error
        throw error
      } finally {
        this.loadingAllGroups = false
      }
    },

    async fetchGroupDetail(groupId, { forceRefresh = false } = {}) {
      if (!groupId) return null

      const cached = this.groupsById[groupId]
      if (!forceRefresh && cached?.milestones) return cached
      if (this.loadingById[groupId]) return cached || null

      this.loadingById = { ...this.loadingById, [groupId]: true }
      this.errorById = { ...this.errorById, [groupId]: null }

      try {
        const auth = useAuthStore()
        const response = await auth.authenticatedFetch(`/groups/${groupId}/`)
        const data = await safeJson(response)
        if (!response.ok) {
          throw new Error(data?.error || '无法获取群组详情')
        }

        this.groupsById[groupId] = data

        const index = this.myGroups.findIndex((group) => group.id === groupId)
        if (index !== -1) {
          const summary = this.myGroups[index]
          this.myGroups[index] = {
            ...summary,
            name: data.name,
            status: data.status,
            mentor: data.mentor,
            track: data.track,
            members: Array.isArray(data.members)
              ? data.members.length
              : summary.members
          }
        }

        return data
      } catch (error) {
        this.errorById = { ...this.errorById, [groupId]: error }
        throw error
      } finally {
        this.loadingById = { ...this.loadingById, [groupId]: false }
      }
    },

    async setTaskCompletion(groupId, taskId, completed) {
      if (!groupId || !taskId) return null

      const auth = useAuthStore()
      const response = await auth.authenticatedFetch(
        `/groups/${groupId}/tasks/${taskId}/`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completed })
        }
      )

      const data = await safeJson(response)
      if (!response.ok) {
        throw new Error(data?.error || '更新任务状态失败')
      }

      const group = this.groupsById[groupId]
      if (group?.milestones) {
        group.milestones.forEach((milestone) => {
          const task = milestone.tasks?.find((t) => t.id === taskId)
          if (task) task.completed = completed
        })
      }

      return data.task
    },

    async addTask(groupId, milestoneId, name) {
      if (!groupId || !milestoneId) return null
      const trimmed = String(name || '').trim()
      if (!trimmed) {
        throw new Error('任务名称不能为空')
      }

      const auth = useAuthStore()
      const response = await auth.authenticatedFetch(
        `/groups/${groupId}/milestones/${milestoneId}/tasks`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: trimmed })
        }
      )

      const data = await safeJson(response)
      if (!response.ok) {
        throw new Error(data?.error || '无法创建任务')
      }

      const group = this.groupsById[groupId]
      if (group?.milestones) {
        const milestone = group.milestones.find(
          (m) => String(m.id) === String(milestoneId)
        )
        if (milestone) {
          if (!Array.isArray(milestone.tasks)) milestone.tasks = []
          milestone.tasks.push(data)
        }
      }

      return data
    }
  }
})
