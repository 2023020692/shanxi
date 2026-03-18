export interface RasterAsset {
  id: string
  filename: string
  original_path: string
  cog_path?: string
  crs?: string
  bbox?: { west: number; south: number; east: number; north: number }
  band_count?: number
  resolution?: number
  status: 'pending' | 'processing' | 'ready' | 'failed'
  created_at: string
  updated_at?: string
}

export interface WellFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: { id: string; name: string; [key: string]: unknown }
}

export interface WellFeatureCollection {
  type: 'FeatureCollection'
  features: WellFeature[]
}

export interface TaskStatus {
  task_id: string
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY' | 'REVOKED'
  result?: unknown
}

export interface Report {
  id: string
  title: string
  raster_id?: string
  file_path?: string
  created_at: string
}
