import { apiClient } from './index'
import type { RasterAsset, EnrichmentGridPoint } from '../types'

export const rasterApi = {
  async list(): Promise<RasterAsset[]> {
    const res = await apiClient.get<RasterAsset[]>('/api/rasters')
    return res.data
  },

  async get(id: string): Promise<RasterAsset> {
    const res = await apiClient.get<RasterAsset>(`/api/rasters/${id}`)
    return res.data
  },

  async upload(file: File): Promise<RasterAsset> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<RasterAsset>('/api/rasters/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  async preprocess(rasterId: string): Promise<{ task_id: string }> {
    const res = await apiClient.post<{ task_id: string }>(`/api/rasters/${rasterId}/preprocess`)
    return res.data
  },

  async getHeatmapGrid(rasterId: string): Promise<{ grid: EnrichmentGridPoint[] }> {
    const res = await apiClient.get<{ grid: EnrichmentGridPoint[] }>(
      `/api/rasters/${rasterId}/heatmap-grid`,
    )
    return res.data
  },
}
