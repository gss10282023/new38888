<template>
  <div class="content-area group-detail" :data-active="activeTab">
    <!-- 顶部信息 -->
    <div class="gd-head">
      <div class="gd-head-left">
        <div class="group-avatars">
          <div class="group-avatar" style="width:48px;height:48px;font-size:1.1rem;">YG</div>
        </div>
        <div>
          <h2 class="gd-title">{{ group?.name || 'Group' }}</h2>
          <p class="gd-subtitle">
            <button
              type="button"
              class="link-button"
              :disabled="!membersList.length"
              @click.stop="toggleMembersList"
            >
              {{ memberCount }} members
            </button>
            <span v-if="group?.mentor?.name">· Mentor: {{ mentorName }}</span>
          </p>
        </div>
      </div>
      <transition name="fade">
        <div
          v-if="showMembersList"
          ref="memberListRef"
          class="member-list"
        >
          <div
            v-for="member in membersList"
            :key="member.id || member.name"
            class="member-list-item"
          >
            <div class="member-list-avatar">{{ getInitials(member.name || member.role) }}</div>
            <div class="member-list-info">
              <div class="member-list-name">{{ member.name || 'Unknown' }}</div>
              <div class="member-list-role">{{ member.role || 'member' }}</div>
            </div>
          </div>
          <button
            type="button"
            class="member-list-close"
            @click="showMembersList = false"
            aria-label="Close members list"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
      </transition>
    </div>

    <!-- 移动端 Tabs（桌面隐藏） -->
    <nav class="mobile-tabs">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'plan' }"
        @click="activeTab = 'plan'"
      >
        Plan
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'discussion' }"
        @click="activeTab = 'discussion'"
      >
        Discussion
      </button>
    </nav>

    <div v-if="errorMessage" class="alert-error">{{ errorMessage }}</div>

    <!-- 桌面：双栏；移动：单栏由 tabs 切换 -->
    <div class="split" :data-active="activeTab">
      <!-- 左栏：Plan -->
      <section class="pane pane--plan card">
        <div class="card-header">
          <h3 class="card-title">Plan</h3>
          <button
            type="button"
            class="btn btn-primary btn-sm"
            :disabled="creatingMilestone"
            @click="createMilestone"
          >
            <i
              class="fas"
              :class="creatingMilestone ? 'fa-spinner fa-spin' : 'fa-plus'"
            ></i>
            <span v-if="creatingMilestone"> Creating…</span>
            <span v-else> Add Milestone</span>
          </button>
        </div>
        <div class="card-content plan-content">
          <div v-if="loading" class="empty-state">Loading plan…</div>
          <div v-else-if="!milestones.length" class="empty-state">No milestones have been created yet.</div>
          <template v-else>
            <div
              v-for="m in milestones"
              :key="m.id"
              class="milestone"
            >
              <div class="milestone-header">
                <div class="milestone-heading">
                  <div class="milestone-title">
                    <i class="fas fa-flag"></i>
                    {{ m.title }}
                  </div>
                  <p v-if="m.description" class="milestone-description">
                    {{ m.description }}
                  </p>
                </div>
                <div class="milestone-actions">
                  <div class="milestone-status">
                    {{ countCompleted(m) }}/{{ (m.tasks || []).length }} Completed
                  </div>
                  <button
                    type="button"
                    class="milestone-delete"
                    title="Delete milestone"
                    :disabled="removingMilestoneId === m.id"
                    @click.stop="deleteMilestone(m)"
                  >
                    <i
                      class="fas"
                      :class="removingMilestoneId === m.id ? 'fa-spinner fa-spin' : 'fa-trash'"
                    ></i>
                  </button>
                </div>
              </div>

              <div class="task-list">
                <div
                  v-for="t in m.tasks"
                  :key="t.id"
                  :class="['task-item', { 'task-item--loading': togglingTaskId === t.id }]"
                  @click="toggleTask(m, t)"
                >
                  <div :class="['task-checkbox', { checked: t.completed }]" />
                  <div :class="['task-label', { completed: t.completed }]">{{ t.name }}</div>
                  <i class="fas fa-calendar" style="color:#6c757d;"></i>
                  <i class="fas fa-user" style="color:#6c757d;"></i>
                </div>

                <div class="add-task-row">
                  <button
                    type="button"
                    class="btn btn-outline btn-sm add-task-btn"
                    :disabled="addingTaskFor === m.id"
                    @click.stop="addTask(m)"
                    title="Add a new task under this milestone"
                  >
                    <i class="fas fa-plus"></i>
                    <span v-if="addingTaskFor === m.id">Adding…</span>
                    <span v-else>Add Task</span>
                  </button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </section>

      <!-- 右栏：Discussion -->
      <section class="pane pane--discussion">
        <div class="chat-container">
          <!-- 讨论区头部改为白色 -->
          <div class="chat-header">
            <h3 style="margin:0;">Discussion Board</h3>
            <button
              v-if="hasMoreMessages"
              type="button"
              class="btn btn-outline btn-xs"
              :disabled="chatLoading || loadingOlder"
              @click="loadOlderMessages"
            >
              <i
                class="fas"
                :class="loadingOlder ? 'fa-spinner fa-spin' : 'fa-history'"
              ></i>
              Load earlier
            </button>
          </div>

          <div v-if="chatErrorMessage" class="alert-error">{{ chatErrorMessage }}</div>

          <div class="chat-messages" ref="msgList">
            <div v-if="chatLoading" class="chat-status">Loading messages…</div>
            <div v-else-if="!displayMessages.length" class="chat-status">No messages yet.</div>
            <template v-else>
              <div
                v-for="message in displayMessages"
                :key="message.id"
                :class="['message', { own: message.isOwn }]"
              >
                <div class="message-avatar">{{ getInitials(message.author) }}</div>
                <div class="message-content">
                  <div class="message-header">
                    <span class="message-author">{{ message.author }}</span>
                    <span class="message-meta">
                      <span class="message-date">{{ formatDate(message.timestamp) }}</span>
                      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                    </span>
                  </div>
                  <div class="message-text">{{ message.text }}</div>
                  <div v-if="message.attachments.length" class="message-attachments">
                    <a
                      v-for="file in message.attachments"
                      :key="file.id"
                      :href="file.url"
                      class="message-attachment-link"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <i class="fas fa-paperclip"></i>
                      {{ file.filename }}
                    </a>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div
            v-if="pendingAttachments.length"
            class="chat-attachments-preview"
          >
            <div
              v-for="file in pendingAttachments"
              :key="file.id"
              :class="['attachment-chip', { uploading: file.uploading, error: !!file.error }]"
            >
              <i
                class="fas"
                :class="file.uploading ? 'fa-spinner fa-spin' : 'fa-paperclip'"
              ></i>
              <span class="attachment-name">{{ file.filename }}</span>
              <button
                type="button"
                class="attachment-remove"
                :disabled="file.uploading"
                @click="removeAttachment(file.id)"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>

          <div v-if="attachmentError" class="alert-error">{{ attachmentError }}</div>

          <div class="chat-input">
            <div class="chat-input-group">
              <textarea
                ref="composer"
                v-model="newMessage"
                class="chat-input-field"
                placeholder="Type your message..."
                rows="2"
                @keydown.enter.exact.prevent="sendMessage"
              ></textarea>
              <div class="chat-actions">
                <input
                  ref="fileInput"
                  type="file"
                  class="sr-only"
                  multiple
                  @change="handleAttachmentSelection"
                />
                <button
                  class="chat-btn chat-btn--secondary"
                  type="button"
                  title="Attach file"
                  aria-label="Attach file"
                  :disabled="isSending || isUploadingAttachment"
                  @click="triggerAttachment"
                >
                  <i
                    class="fas"
                    :class="isUploadingAttachment ? 'fa-spinner fa-spin' : 'fa-paperclip'"
                  ></i>
                </button>
                <button
                  class="chat-btn chat-btn--primary"
                  type="button"
                  @click="sendMessage"
                  title="Send"
                  aria-label="Send message"
                  :disabled="disableSendButton || isSending || isUploadingAttachment"
                >
                  <i
                    class="fas"
                    :class="isSending ? 'fa-spinner fa-spin' : 'fa-paper-plane'"
                  ></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGroupStore } from '@/stores/groups'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const groupStore = useGroupStore()
const chatStore = useChatStore()
const authStore = useAuthStore()

const groupId = computed(() => route.params.id)
const group = computed(() => groupStore.groupsById[groupId.value])

// layout + group info
const activeTab = ref('plan')
const loading = ref(false)
const errorMessage = ref('')
const togglingTaskId = ref(null)
const addingTaskFor = ref(null)
const creatingMilestone = ref(false)
const removingMilestoneId = ref(null)

const milestones = computed(() => group.value?.milestones || [])
const memberCount = computed(() =>
  Array.isArray(group.value?.members) ? group.value.members.length : 0
)
const mentorName = computed(() => group.value?.mentor?.name || '—')
const membersList = computed(() =>
  Array.isArray(group.value?.members) ? group.value.members : []
)
const showMembersList = ref(false)
const memberListRef = ref(null)

// chat state
const newMessage = ref('')
const composer = ref(null)
const msgList = ref(null)
const fileInput = ref(null)
const pendingAttachments = ref([])
const attachmentError = ref('')
const chatMessageError = ref('')

const chatMessages = computed(() => chatStore.messagesByGroup[groupId.value] || [])
const chatLoading = computed(() => !!chatStore.loadingByGroup[groupId.value])
const hasMoreMessages = computed(() => !!chatStore.hasMoreByGroup[groupId.value])
const chatStoreError = computed(() => chatStore.errorByGroup[groupId.value])
const isSending = computed(() => !!chatStore.sendingByGroup[groupId.value])
const loadingOlder = ref(false)

const chatErrorMessage = computed(() => {
  if (chatMessageError.value) return chatMessageError.value
  const err = chatStoreError.value
  if (!err) return ''
  return err.message || `${err}`
})

const isUploadingAttachment = computed(() =>
  pendingAttachments.value.some((item) => item.uploading)
)

const readyAttachments = computed(() =>
  pendingAttachments.value.filter((item) => item.url && !item.uploading && !item.error)
)

const disableSendButton = computed(
  () => !newMessage.value.trim() && readyAttachments.value.length === 0
)

const displayMessages = computed(() =>
  chatMessages.value.map((message) => {
    const timestamp = message.timestamp
    const attachments = Array.isArray(message.attachments) ? message.attachments : []
    return {
      id: message.id,
      author: message.author?.name || message.author || 'Unknown',
      authorId: message.author?.id ?? null,
      text: message.text || '',
      timestamp,
      attachments: attachments.map((file, index) => ({
        id: `${message.id}-${index}`,
        url: file.file_url || file.url,
        filename: file.filename || 'Attachment',
        size: file.file_size || file.size || null,
        mimeType: file.mime_type || file.mimeType || 'application/octet-stream'
      })),
      isOwn: authStore.user?.id
        ? message.author?.id === authStore.user.id
        : false
    }
  })
)

const getInitials = (name) =>
  String(name || '')
    .split(' ')
    .filter(Boolean)
    .map((segment) => segment[0])
    .join('')
    .toUpperCase() || '—'

const formatDate = (value) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatTime = (value) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = async () => {
  await nextTick()
  if (msgList.value) {
    msgList.value.scrollTop = msgList.value.scrollHeight
  }
}

const focusComposer = () => composer.value?.focus()

const loadGroup = async (id, { force = false } = {}) => {
  if (!id) return
  loading.value = true
  errorMessage.value = ''
  try {
    if (!groupStore.myGroupsLoaded) {
      await groupStore.fetchMyGroups()
    }
    await groupStore.fetchGroupDetail(id, { forceRefresh: force })
  } catch (error) {
    console.error('Failed to load group detail', error)
    errorMessage.value = error?.message || 'Failed to load group information'
  } finally {
    loading.value = false
  }
}

const loadChat = async (
  id,
  { before = null, append = false } = {}
) => {
  if (!id) return
  chatMessageError.value = ''
  try {
    await chatStore.fetchMessages(id, { before, append })
    if (!append) {
      await scrollToBottom()
    }
  } catch (error) {
    console.error('Failed to load chat messages', error)
    chatMessageError.value = error?.message || 'Failed to load chat messages'
  }
}

const loadOlderMessages = async () => {
  if (!groupId.value || !hasMoreMessages.value || loadingOlder.value) return
  const oldest = chatMessages.value[0]
  if (!oldest?.timestamp) return
  loadingOlder.value = true
  try {
    await loadChat(groupId.value, { before: oldest.timestamp, append: true })
  } finally {
    loadingOlder.value = false
  }
}

const triggerAttachment = () => {
  attachmentError.value = ''
  chatMessageError.value = ''
  fileInput.value?.click()
}

const patchAttachment = (id, patch) => {
  pendingAttachments.value = pendingAttachments.value.map((item) =>
    item.id === id ? { ...item, ...patch } : item
  )
}

const handleAttachmentSelection = async (event) => {
  const files = Array.from(event.target?.files || [])
  event.target.value = ''
  if (!files.length) return

  attachmentError.value = ''
  chatMessageError.value = ''

  for (const file of files) {
    const entry = {
      id: `${Date.now()}-${file.name}-${Math.random().toString(36).slice(2)}`,
      filename: file.name,
      size: file.size,
      mimeType: file.type || 'application/octet-stream',
      uploading: true,
      url: null,
      error: null
    }
    pendingAttachments.value = [...pendingAttachments.value, entry]

    try {
      const uploaded = await chatStore.uploadAttachment(file)
      patchAttachment(entry.id, {
        url: uploaded.url,
        filename: uploaded.filename,
        size: uploaded.size,
        mimeType: uploaded.mimeType,
        uploading: false,
        error: null
      })
    } catch (error) {
      const message = error?.message || 'File upload failed'
      patchAttachment(entry.id, {
        uploading: false,
        error: message
      })
      attachmentError.value = message
      console.error('Failed to upload attachment', error)
    }
  }
}

const removeAttachment = (id) => {
  pendingAttachments.value = pendingAttachments.value.filter((item) => item.id !== id)
}

const sendMessage = async () => {
  const text = newMessage.value.trim()
  if (disableSendButton.value) return
  if (isUploadingAttachment.value) {
    attachmentError.value = 'File upload is still in progress, please wait'
    return
  }

  chatMessageError.value = ''
  attachmentError.value = ''

  try {
    await chatStore.sendMessage(groupId.value, {
      text,
      attachments: readyAttachments.value.map((item) => ({
        url: item.url,
        filename: item.filename,
        size: item.size,
        mimeType: item.mimeType
      }))
    })
    newMessage.value = ''
    pendingAttachments.value = []
    await scrollToBottom()
    focusComposer()
  } catch (error) {
    chatMessageError.value = error?.message || 'Failed to send message'
    console.error('Failed to send message', error)
  }
}

watch(
  groupId,
  (id) => {
    if (!id) return
    showMembersList.value = false
    loadGroup(id)
    loadChat(id, { append: false })
  },
  { immediate: true }
)

watch(memberCount, (count) => {
  if (!count) showMembersList.value = false
})

watch(chatMessages, async () => {
  if (loadingOlder.value) return
  await scrollToBottom()
})

const countCompleted = (milestone) =>
  Array.isArray(milestone?.tasks)
    ? milestone.tasks.filter((task) => task.completed).length
    : 0

const toggleTask = async (milestone, task) => {
  if (!groupId.value || !task) return
  if (togglingTaskId.value === task.id) return

  errorMessage.value = ''
  const previous = task.completed
  const nextState = !previous
  task.completed = nextState
  togglingTaskId.value = task.id

  try {
    await groupStore.setTaskCompletion(groupId.value, task.id, nextState)
  } catch (error) {
    task.completed = previous
    errorMessage.value = error?.message || 'Failed to update task'
    console.error('Failed to update task', error)
  } finally {
    togglingTaskId.value = null
  }
}

const addTask = async (milestone) => {
  if (!groupId.value || !milestone) return
  const name = window.prompt('Enter a task name', 'New Task')
  if (!name) return

  errorMessage.value = ''
  addingTaskFor.value = milestone.id
  try {
    await groupStore.addTask(groupId.value, milestone.id, name)
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to create task'
    console.error('Failed to create task', error)
  } finally {
    addingTaskFor.value = null
  }
}

const createMilestone = async () => {
  if (!groupId.value) return
  const title = window.prompt('Enter a milestone title', 'New Milestone')
  if (!title) return
  const descriptionPrompt = window.prompt('Optional description (leave blank to skip)', '')
  const description = descriptionPrompt == null ? '' : descriptionPrompt

  errorMessage.value = ''
  creatingMilestone.value = true
  try {
    await groupStore.createMilestone(groupId.value, {
      title,
      description
    })
    await loadGroup(groupId.value, { force: true })
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to create milestone'
    console.error('Failed to create milestone', error)
  } finally {
    creatingMilestone.value = false
  }
}

const deleteMilestone = async (milestone) => {
  if (!groupId.value || !milestone) return
  const confirmed = window.confirm(`Delete milestone "${milestone.title}"? This cannot be undone.`)
  if (!confirmed) return

  errorMessage.value = ''
  removingMilestoneId.value = milestone.id
  try {
    await groupStore.deleteMilestone(groupId.value, milestone.id)
    await loadGroup(groupId.value, { force: true })
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to delete milestone'
    console.error('Failed to delete milestone', error)
  } finally {
    removingMilestoneId.value = null
  }
}

const toggleMembersList = () => {
  if (!membersList.value.length) return
  showMembersList.value = !showMembersList.value
}

const handleOutsideClick = (event) => {
  if (!showMembersList.value) return
  const container = memberListRef.value
  if (!container) return
  if (!container.contains(event.target)) {
    showMembersList.value = false
  }
}

onMounted(() => {
  focusComposer()
  if (chatMessages.value.length) {
    scrollToBottom()
  }
  document.addEventListener('click', handleOutsideClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style scoped>
/* 顶部信息 */
.gd-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}
.gd-head-left {
  display: flex;
  align-items: center;
  gap: 0.9rem;
}
.gd-title { margin: 0; color: var(--charcoal); }
.gd-subtitle { color: #6c757d; margin-top: 0.15rem; }
.link-button {
  border: none;
  background: none;
  color: var(--dark-green);
  font-weight: 600;
  padding: 0;
  cursor: pointer;
}
.link-button:hover:not(:disabled) {
  text-decoration: underline;
}
.link-button:disabled {
  color: #b0b5b9;
  cursor: not-allowed;
}

.member-list {
  margin-top: 0.75rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  background-color: #fff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  position: relative;
  max-width: 340px;
}
.member-list-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.45rem 0;
}
.member-list-item + .member-list-item {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.member-list-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--mint-green);
  color: var(--charcoal);
  display: grid;
  place-items: center;
  font-weight: 600;
}
.member-list-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.member-list-name {
  font-weight: 600;
  color: var(--charcoal);
}
.member-list-role {
  font-size: 0.8rem;
  color: #6c757d;
  text-transform: capitalize;
}
.member-list-close {
  position: absolute;
  top: 6px;
  right: 6px;
  border: none;
  background: transparent;
  color: #6c757d;
  cursor: pointer;
}
.member-list-close:hover {
  color: var(--charcoal);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 移动端 tabs（桌面隐藏） */
.mobile-tabs {
  display: none;
  gap: 0.75rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 0.5rem;
}
.tab-btn {
  background: transparent;
  border: none;
  padding: 0.5rem 0.25rem;
  color: var(--charcoal);
  font-weight: 500;
  border-bottom: 3px solid transparent;
  cursor: pointer;
}
.tab-btn.active {
  color: var(--dark-green);
  border-bottom-color: var(--dark-green);
}

/* 双栏布局容器 */
.split {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 1.5rem;
  align-items: stretch;
  max-height: 70vh;
  height: 70vh;
}

/* 左栏：Plan */
.pane--plan {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 320px;
}

/* 右栏：Discussion */
.pane--discussion {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 320px;
}

/* 卡片样式 */
.card {
  height: 100%;
  min-height: 320px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.card-content {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
}
.plan-content {
  padding-right: 2px; /* for visible scrollbar */
}

.milestone {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 1.1rem 1.25rem;
  background: var(--white);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.milestone + .milestone {
  margin-top: 1rem;
}

.milestone-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.milestone-heading {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.milestone-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: var(--charcoal);
}

.milestone-title i {
  color: var(--dark-green);
}

.milestone-description {
  margin: 0;
  color: #6c757d;
  font-size: 0.9rem;
  line-height: 1.4;
}

.milestone-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.milestone-status {
  padding: 0.25rem 0.65rem;
  background: rgba(1, 113, 81, 0.1);
  color: var(--dark-green);
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
}

.milestone-delete {
  border: none;
  background: transparent;
  color: #d9534f;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.15rem;
  transition: opacity 0.2s ease;
  font-size: 1rem;
}

.milestone-delete:hover:not(:disabled) {
  opacity: 0.75;
}

.milestone-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Add Task 行的微调，保持与全站按钮风格一致 */
.add-task-row {
  padding-left: 0.25rem;
  margin-top: 0.4rem;
}
.add-task-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border-color: var(--border-light);
}

/* Discussion board layout & chat styling */
.pane--discussion .chat-container {
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-height: 0;
  background: var(--white);
  border-radius: var(--radius-xl);
  border: 1.5px solid var(--border-lighter);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: var(--white);
  border-bottom: 1px solid var(--border-light);
}

.chat-messages {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: linear-gradient(
    180deg,
    var(--bg-lighter) 0%,
    rgba(255, 255, 255, 0.95) 30%,
    var(--white) 100%
  );
}

.message {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  max-width: 100%;
}

.message.own {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--mint-green) 0%, var(--eucalypt) 100%);
  color: var(--white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.95rem;
  box-shadow: 0 6px 16px rgba(113, 163, 153, 0.35);
  flex-shrink: 0;
}

.message.own .message-avatar {
  background: linear-gradient(135deg, var(--dark-green) 0%, #018a63 100%);
  box-shadow: none;
}

.message-content {
  max-width: min(100%, 520px);
  background: var(--white);
  padding: 0.85rem 1rem;
  border-radius: 16px 16px 16px 6px;
  border: 1px solid var(--border-lighter);
  box-shadow: 0 8px 24px rgba(1, 113, 81, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.message.own .message-content {
  background: linear-gradient(135deg, var(--dark-green) 0%, #0d8a66 100%);
  color: var(--white);
  border-color: transparent;
  border-radius: 16px 6px 16px 16px;
  align-items: flex-end;
  box-shadow: 0 8px 20px rgba(1, 113, 81, 0.25);
}

.message-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
}

.message-author {
  font-weight: 600;
  color: var(--charcoal);
  font-size: 0.95rem;
}

.message.own .message-author {
  color: var(--white);
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6c757d;
}

.message-date {
  font-weight: 500;
}

.message.own .message-meta {
  color: rgba(255, 255, 255, 0.75);
}

.message-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: inherit;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-attachments {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  align-items: flex-start;
}

.message-attachment-link {
  color: inherit;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.55rem;
  border-radius: var(--radius-sm);
  background: rgba(1, 113, 81, 0.08);
}

.message-attachment-link:hover {
  text-decoration: none;
  background: rgba(1, 113, 81, 0.16);
}

.message.own .message-attachments {
  align-items: flex-end;
}

.message.own .message-attachment-link {
  background: rgba(255, 255, 255, 0.18);
}

.chat-status {
  padding: 1.5rem;
  text-align: center;
  color: #7a869a;
  font-size: 0.95rem;
  font-weight: 500;
}

.chat-attachments-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  padding: 0.75rem 1.5rem;
  background: var(--bg-lighter);
  border-top: 1px solid var(--border-lighter);
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  background: var(--white);
  border: 1.5px solid var(--border-lighter);
  box-shadow: 0 4px 12px rgba(1, 113, 81, 0.12);
  font-size: 0.85rem;
  color: var(--charcoal);
}

.attachment-chip.uploading {
  opacity: 0.7;
}

.attachment-chip.error {
  border-color: #f3c0c0;
  color: #a52727;
}

.attachment-name {
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-remove {
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}

.attachment-remove:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.chat-input {
  border-top: 1px solid var(--border-lighter);
  background: var(--white);
  padding: 1rem 1.5rem 1.5rem;
}

.chat-input-group {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  border: 1.5px solid var(--border-lighter);
  border-radius: var(--radius-lg);
  padding: 0.75rem 1rem;
  background: var(--bg-lighter);
}

.chat-input-field {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--charcoal);
  max-height: 160px;
}

.chat-input-field:focus {
  outline: none;
}

.chat-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chat-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  transition: var(--transition);
}

.chat-btn--secondary {
  background: rgba(1, 113, 81, 0.12);
  color: var(--dark-green);
}

.chat-btn--secondary:hover:not(:disabled) {
  background: rgba(1, 113, 81, 0.2);
}

.chat-btn--primary {
  background: linear-gradient(135deg, var(--dark-green) 0%, #028f68 100%);
  color: var(--white);
  box-shadow: 0 8px 18px rgba(1, 113, 81, 0.25);
}

.chat-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 12px 26px rgba(1, 113, 81, 0.3);
}

.chat-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.alert-error {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background-color: #ffecec;
  border: 1px solid #f3c0c0;
  color: #a52727;
  border-radius: 8px;
}

.empty-state {
  padding: 1.5rem 1rem;
  text-align: center;
  color: #6c757d;
}

.task-item--loading {
  opacity: 0.6;
  pointer-events: none;
}

/* 移动端：单列 + 由 tabs 控制显示哪一块 */
@media (max-width: 900px) {
  .split {
    grid-template-columns: 1fr;
    max-height: 80vh;
    height: 80vh;
  }
  .mobile-tabs { display: flex; }
  .split .pane { display: none; }
  .split[data-active="plan"] .pane--plan { display: block; }
  .split[data-active="discussion"] .pane--discussion { display: block; }
  .card {
    min-height: 220px;
  }
}

@media (max-width: 700px) {
  .chat-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .chat-input {
    padding: 0.85rem 1rem 1.2rem;
  }

  .chat-input-group {
    flex-direction: column;
    align-items: stretch;
    gap: 0.65rem;
  }

  .chat-actions {
    justify-content: flex-end;
  }

  .chat-btn {
    width: 38px;
    height: 38px;
  }
}
</style>
