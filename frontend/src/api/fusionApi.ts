import { apiClient } from './index'

export interface FusionJob {
  id: string
  type: string
  status: string
  result?: {
    name?: string
    raster_ids?: string[]
    method?: 'overlay' | 'weighted_sum' | 'mean'
    [key: string]: unknown
  }
  created_at: string
}

export const fusionApi = {
  async create(name: string, rasterIds: string[], method: 'overlay' | 'weighted_sum' | 'mean'): Promise<FusionJob> {
    const res = await apiClient.post<FusionJob>('/api/fusion/jobs', {
      name,
      raster_ids: rasterIds,
      method,
    })
    return res.data
  },

  async list(): Promise<FusionJob[]> {
    const res = await apiClient.get<FusionJob[]>('/api/fusion/jobs')
    return res.data
  },

  async get(jobId: string): Promise<FusionJob> {
    const res = await apiClient.get<FusionJob>(`/api/fusion/jobs/${jobId}`)
    return res.data
  },
}
