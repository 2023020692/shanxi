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

export interface CrossValidateResult {
  validation_id: string
  raster_id: string
  reference_dataset: string
  reference_dataset_name: string
  r_value: number
  r_squared: number
  rmse: number
  sample_count: number
  status: string
  message: string
}

export interface EnrichmentResultItem {
  id: string
  name: string
  raster_ids: string[]
  method: string
  method_name: string
  status: string
  enrichment_index?: number
  high_value_ratio?: number
  coverage_area_km2?: number
  colormap: string
  created_at: string
}

export interface EnrichmentGridPoint {
  lon: number
  lat: number
  value: number
}

export interface SAM2Result {
  detection_id: string
  filename: string
  file_size_bytes: number
  model: string
  status: string
  detection_count: number
  detections: Array<{
    x1: number; y1: number; x2: number; y2: number
    confidence: number; label: string
  }>
  heatmap_grid: Array<{ lon: number; lat: number; intensity: number }>
  message: string
  created_at?: string
}
