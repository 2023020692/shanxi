import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TaskStatus } from '../types'
import { taskApi } from '../api/taskApi'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Record<string, TaskStatus>>({})

  async function pollTask(taskId: string) {
    const result = await taskApi.getStatus(taskId)
    tasks.value[taskId] = result
    return result
  }

  return { tasks, pollTask }
})
