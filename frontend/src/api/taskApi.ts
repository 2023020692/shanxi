import { apiClient } from './index'
import type { TaskStatus } from '../types'

export const taskApi = {
  async getStatus(taskId: string): Promise<TaskStatus> {
    const res = await apiClient.get<TaskStatus>(`/api/tasks/${taskId}`)
    return res.data
  },
}
