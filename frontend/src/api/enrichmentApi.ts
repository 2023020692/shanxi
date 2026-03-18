import { apiClient } from './index'
import type { EnrichmentResultItem, EnrichmentGridPoint } from '../types'

export const enrichmentApi = {
  async analyze(
    name: string,
    rasterIds: string[],
    method: string,
  ): Promise<EnrichmentResultItem> {
    const res = await apiClient.post<EnrichmentResultItem>('/api/enrichment/analyze', {
      name,
      raster_ids: rasterIds,
      method,
    })
    return res.data
  },

  async list(): Promise<EnrichmentResultItem[]> {
    const res = await apiClient.get<EnrichmentResultItem[]>('/api/enrichment/results')
    return res.data
  },

  async getGrid(resultId: string): Promise<{ grid: EnrichmentGridPoint[] }> {
    const res = await apiClient.get<{ grid: EnrichmentGridPoint[] }>(
      `/api/enrichment/results/${resultId}`,
    )
    return res.data
  },
}
