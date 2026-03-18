import { apiClient } from './index'
import type { WellFeatureCollection } from '../types'

export const wellApi = {
  async list(): Promise<WellFeatureCollection> {
    const res = await apiClient.get<WellFeatureCollection>('/api/wells')
    return res.data
  },

  async importExcel(file: File): Promise<{ imported: number }> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<{ imported: number }>('/api/wells/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },
}
