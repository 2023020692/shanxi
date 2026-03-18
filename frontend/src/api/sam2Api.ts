import { apiClient } from './index'
import type { SAM2Result } from '../types'

export const sam2Api = {
  async detect(file: File): Promise<SAM2Result> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<SAM2Result>('/api/ai/detect', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  async info(): Promise<Record<string, unknown>> {
    const res = await apiClient.get('/api/ai/info')
    return res.data
  },

  async list(): Promise<SAM2Result[]> {
    const res = await apiClient.get<SAM2Result[]>('/api/ai/results')
    return res.data
  },

  async get(detectionId: string): Promise<SAM2Result> {
    const res = await apiClient.get<SAM2Result>(`/api/ai/results/${detectionId}`)
    return res.data
  },
}
