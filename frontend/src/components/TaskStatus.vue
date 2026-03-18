<template>
  <div class="task-status">
    <div class="status-row">
      <el-icon :class="iconClass"><component :is="statusIcon" /></el-icon>
      <span class="status-text" :class="textClass">{{ statusLabel }}</span>
    </div>
    <p v-if="taskId" class="task-id">Task ID: {{ taskId }}</p>
    <div v-if="result" class="task-result">
      <pre>{{ JSON.stringify(result, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { Loading, Check, Close, Clock } from '@element-plus/icons-vue'
import { taskApi } from '../api/taskApi'
import type { TaskStatus as TaskStatusType } from '../types'

const props = defineProps<{ taskId: string }>()

const taskStatus = ref<TaskStatusType | null>(null)
let pollInterval: ReturnType<typeof setInterval> | null = null

const result = computed(() => taskStatus.value?.result)

const statusLabel = computed(() => {
  switch (taskStatus.value?.status) {
    case 'PENDING': return '等待中'
    case 'STARTED': return '处理中'
    case 'SUCCESS': return '完成'
    case 'FAILURE': return '失败'
    default: return taskStatus.value?.status || '未知'
  }
})

const statusIcon = computed(() => {
  switch (taskStatus.value?.status) {
    case 'PENDING': return Clock
    case 'STARTED': return Loading
    case 'SUCCESS': return Check
    case 'FAILURE': return Close
    default: return Clock
  }
})

const iconClass = computed(() => ({
  'is-loading': taskStatus.value?.status === 'STARTED',
}))

const textClass = computed(() => ({
  'text-success': taskStatus.value?.status === 'SUCCESS',
  'text-danger': taskStatus.value?.status === 'FAILURE',
  'text-warning': taskStatus.value?.status === 'STARTED' || taskStatus.value?.status === 'PENDING',
}))

async function poll() {
  try {
    taskStatus.value = await taskApi.getStatus(props.taskId)
    if (taskStatus.value.status === 'SUCCESS' || taskStatus.value.status === 'FAILURE') {
      stopPolling()
    }
  } catch (e) {
    console.error(e)
  }
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

watch(() => props.taskId, (newId) => {
  if (newId) {
    stopPolling()
    poll()
    pollInterval = setInterval(poll, 3000)
  }
}, { immediate: true })

onUnmounted(stopPolling)
</script>

<style scoped>
.task-status {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-text {
  font-size: 14px;
  font-weight: 500;
}

.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
.text-warning { color: #e6a23c; }

.task-id {
  font-size: 11px;
  color: #aaa;
  margin-top: 4px;
  word-break: break-all;
}

.task-result pre {
  font-size: 11px;
  background: #fff;
  padding: 6px;
  border-radius: 4px;
  margin-top: 4px;
  overflow: auto;
  max-height: 100px;
}
</style>
