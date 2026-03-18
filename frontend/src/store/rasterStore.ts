import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RasterAsset } from '../types'
import { rasterApi } from '../api/rasterApi'

export const useRasterStore = defineStore('raster', () => {
  const rasters = ref<RasterAsset[]>([])
  const loading = ref(false)

  async function fetchRasters() {
    loading.value = true
    try {
      rasters.value = await rasterApi.list()
    } finally {
      loading.value = false
    }
  }

  return { rasters, loading, fetchRasters }
})
