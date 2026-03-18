import { apiClient } from './index'
import type { Report } from '../types'

export interface GenerateReportRequest {
  title?: string
  raster_id?: string | null
  enrichment_result_ids?: string[]
  sam2_detection_id?: string | null
  ai_analysis_text?: string | null
}

export const reportApi = {
  async list(): Promise<Report[]> {
    const res = await apiClient.get<Report[]>('/api/reports')
    return res.data
  },

  async generate(req: GenerateReportRequest): Promise<Report> {
    const res = await apiClient.post<Report>('/api/reports/generate', {
      title: req.title || '煤矿资源分析系统数据分析报告',
      raster_id: req.raster_id || null,
      enrichment_result_ids: req.enrichment_result_ids || [],
      sam2_detection_id: req.sam2_detection_id || null,
      ai_analysis_text: req.ai_analysis_text || null,
    })
    return res.data
  },

  downloadUrl(reportId: string): string {
    return `/api/reports/${reportId}/download`
  },
}
