import { apiClient } from './index'
import type { SAM2Result, SatelliteImage, SAM2Raster } from '../types'

export const sam2Api = {
  async detect(file: File): Promise<SAM2Result> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<SAM2Result>('/api/ai/detect', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  async info(): Promise<Record<string, unknown>> {
    const res = await apiClient.get('/api/ai/info')
    return res.data
  },

  async list(): Promise<SAM2Result[]> {
    const res = await apiClient.get<SAM2Result[]>('/api/ai/results')
    return res.data
  },

  async get(detectionId: string): Promise<SAM2Result> {
    const res = await apiClient.get<SAM2Result>(`/api/ai/results/${detectionId}`)
    return res.data
  },

  async analyzeImage(file: File): Promise<SatelliteImage> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<SatelliteImage>('/api/ai/analyze-image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  async listSatelliteImages(): Promise<SatelliteImage[]> {
    const res = await apiClient.get<SatelliteImage[]>('/api/ai/satellite-images')
    return res.data
  },

  async analyzeTif(file: File): Promise<SAM2Raster> {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<SAM2Raster>('/api/ai/analyze-tif', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  async listSAM2Rasters(): Promise<SAM2Raster[]> {
    const res = await apiClient.get<SAM2Raster[]>('/api/ai/sam2-rasters')
    return res.data
  },
}
