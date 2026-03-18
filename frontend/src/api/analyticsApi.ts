import { apiClient } from './index'

export interface HeatgridFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: { count: number; lon: number; lat: number }
}

export interface HeatgridResult {
  type: 'FeatureCollection'
  features: HeatgridFeature[]
  total_wells: number
  grid_cells: number
}

export interface SummaryResult {
  well_count: number
  raster_stats: Record<string, number>
  report_count: number
}

export const analyticsApi = {
  async getHeatgrid(resolution = 0.5): Promise<HeatgridResult> {
    const res = await apiClient.get<HeatgridResult>('/api/analytics/heatgrid', {
      params: { resolution },
    })
    return res.data
  },

  async getSummary(): Promise<SummaryResult> {
    const res = await apiClient.get<SummaryResult>('/api/analytics/summary')
    return res.data
  },
}
