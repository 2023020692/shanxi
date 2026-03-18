import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WellFeatureCollection } from '../types'
import { wellApi } from '../api/wellApi'

export const useWellStore = defineStore('well', () => {
  const wells = ref<WellFeatureCollection | null>(null)
  const loading = ref(false)

  async function fetchWells() {
    loading.value = true
    try {
      wells.value = await wellApi.list()
    } finally {
      loading.value = false
    }
  }

  return { wells, loading, fetchWells }
})
