import { apiClient } from './index'
import type { Report } from '../types'

export const reportApi = {
  async list(): Promise<Report[]> {
    const res = await apiClient.get<Report[]>('/api/reports')
    return res.data
  },

  async generate(title: string, rasterId?: string): Promise<Report> {
    const res = await apiClient.post<Report>('/api/reports/generate', {
      title,
      raster_id: rasterId || null,
    })
    return res.data
  },

  downloadUrl(reportId: string): string {
    return `/api/reports/${reportId}/download`
  },
}
