import { defineStore } from 'pinia'
import { safeJson } from '@/utils/http'
import { useAuthStore } from '@/stores/auth'

const DEFAULT_LIMIT = 50

export const useChatStore = defineStore('chat', {
  state: () => ({
    messagesByGroup: {},
    loadingByGroup: {},
    hasMoreByGroup: {},
    errorByGroup: {},
    sendingByGroup: {},
    uploadingFiles: {}
  }),
  actions: {
    reset() {
      this.messagesByGroup = {}
      this.loadingByGroup = {}
      this.hasMoreByGroup = {}
      this.errorByGroup = {}
      this.sendingByGroup = {}
      this.uploadingFiles = {}
    },

    normaliseMessages(raw = []) {
      return [...raw]
        .map((item) => ({
          id: item.id,
          text: item.text || '',
          timestamp: item.timestamp,
          author: {
            id: item.author?.id ?? null,
            name: item.author?.name || item.author || 'Unknown'
          },
          attachments: Array.isArray(item.attachments) ? item.attachments : []
        }))
        .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    },

    async fetchMessages(groupId, { before = null, limit = DEFAULT_LIMIT, append = false } = {}) {
      if (!groupId) return []
      const auth = useAuthStore()

      if (this.loadingByGroup[groupId]) {
        return this.messagesByGroup[groupId] || []
      }

      this.loadingByGroup = { ...this.loadingByGroup, [groupId]: true }
      this.errorByGroup = { ...this.errorByGroup, [groupId]: null }

      const params = new URLSearchParams()
      if (limit) params.set('limit', limit)
      if (before) params.set('before', before)

      try {
        const response = await auth.authenticatedFetch(
          `/groups/${groupId}/messages${params.toString() ? `?${params}` : ''}`
        )
        const data = await safeJson(response)
        if (!response.ok) {
          throw new Error(data?.error || '无法获取消息列表')
        }

        const normalised = this.normaliseMessages(data?.messages)

        if (append && Array.isArray(this.messagesByGroup[groupId])) {
          const merged = [...normalised, ...this.messagesByGroup[groupId]]
          const deduped = []
          const seen = new Set()
          merged.forEach((message) => {
            if (!seen.has(message.id)) {
              seen.add(message.id)
              deduped.push(message)
            }
          })
          this.messagesByGroup = { ...this.messagesByGroup, [groupId]: deduped }
        } else {
          this.messagesByGroup = { ...this.messagesByGroup, [groupId]: normalised }
        }

        this.hasMoreByGroup = { ...this.hasMoreByGroup, [groupId]: !!data?.hasMore }
        return this.messagesByGroup[groupId]
      } catch (error) {
        this.errorByGroup = { ...this.errorByGroup, [groupId]: error }
        throw error
      } finally {
        this.loadingByGroup = { ...this.loadingByGroup, [groupId]: false }
      }
    },

    async sendMessage(groupId, { text = '', attachments = [] } = {}) {
      if (!groupId) throw new Error('缺少群组 ID')
      const auth = useAuthStore()

      if (this.sendingByGroup[groupId]) {
        throw new Error('正在发送上一条消息，请稍等')
      }
      this.sendingByGroup = { ...this.sendingByGroup, [groupId]: true }

      const payload = {
        text,
        attachments: attachments.map((item) => ({
          url: item.url,
          filename: item.filename,
          size: item.size,
          mimeType: item.mimeType || item.mime_type || 'application/octet-stream'
        }))
      }

      try {
        const response = await auth.authenticatedFetch(`/groups/${groupId}/messages`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        const data = await safeJson(response)
        if (!response.ok) {
          throw new Error(data?.error || '发送消息失败')
        }

        const normalised = this.normaliseMessages([data])
        const existing = this.messagesByGroup[groupId] || []
        const merged = [...existing, ...normalised]
        const deduped = []
        const seen = new Set()
        merged.forEach((message) => {
          if (!seen.has(message.id)) {
            seen.add(message.id)
            deduped.push(message)
          }
        })
        this.messagesByGroup = { ...this.messagesByGroup, [groupId]: deduped }
        return normalised[0]
      } finally {
        this.sendingByGroup = { ...this.sendingByGroup, [groupId]: false }
      }
    },

    async uploadAttachment(file) {
      if (!file) throw new Error('没有选择文件')
      const auth = useAuthStore()
      const tmpId = `${Date.now()}-${file.name}`
      this.uploadingFiles = {
        ...this.uploadingFiles,
        [tmpId]: { file, status: 'uploading' }
      }

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await auth.authenticatedFetch('/uploads/', {
          method: 'POST',
          body: formData
        })
        const data = await safeJson(response)
        if (!response.ok || !data?.url) {
          throw new Error(data?.error || '上传失败')
        }

        this.uploadingFiles = {
          ...this.uploadingFiles,
          [tmpId]: { file, status: 'done', result: data }
        }
        return {
          url: data.url,
          filename: data.filename || file.name,
          size: data.size || file.size,
          mimeType: data.mimeType || file.type || 'application/octet-stream'
        }
      } catch (error) {
        this.uploadingFiles = {
          ...this.uploadingFiles,
          [tmpId]: { file, status: 'error', error }
        }
        throw error
      }
    }
  }
})
