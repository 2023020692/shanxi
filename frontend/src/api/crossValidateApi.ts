import { apiClient } from './index'
import type { CrossValidateResult } from '../types'

export const REFERENCE_DATASETS = [
  { key: 'GNSS', name: 'GNSS定位数据' },
  { key: 'SMOS', name: 'SMOS土壤水分数据' },
  { key: 'CERES', name: 'CERES辐射数据' },
  { key: 'GOSAT', name: 'GOSAT温室气体数据' },
  { key: 'MODIS_VIIRS', name: 'MODIS/VIIRS遥感数据' },
  { key: 'AVIRIS_NG', name: 'AVIRIS NG高光谱数据' },
]

export const crossValidateApi = {
  async validate(rasterId: string, referenceDataset: string): Promise<CrossValidateResult> {
    const res = await apiClient.post<CrossValidateResult>('/api/cross-validation/validate', {
      raster_id: rasterId,
      reference_dataset: referenceDataset,
    })
    return res.data
  },
}
