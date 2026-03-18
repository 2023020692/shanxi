<template>
  <div class="layer-panel">
    <div class="panel-actions">
      <el-button type="primary" size="small" @click="fetchRasters" :loading="loading">
        刷新列表
      </el-button>
    </div>

    <el-empty v-if="rasters.length === 0 && !loading" description="暂无栅格数据" />

    <div v-for="raster in rasters" :key="raster.id" class="raster-item">
      <div class="raster-info">
        <span class="raster-name" :title="raster.filename">{{ raster.filename }}</span>
        <el-tag :type="statusType(raster.status)" size="small">{{ raster.status }}</el-tag>
      </div>

      <div v-if="raster.status === 'ready'" class="raster-controls">
        <el-select v-model="selectedColormap[raster.id]" size="small" placeholder="颜色方案" style="width: 120px">
          <el-option v-for="c in colormaps" :key="c" :label="c" :value="c" />
        </el-select>
        <el-button size="small" type="success" @click="loadToMap(raster)">加载到地图</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { RasterAsset } from '../types'
import { rasterApi } from '../api/rasterApi'

const props = defineProps<{ mapViewRef: { addRasterLayer: (url: string, name: string) => void } | null }>()

const rasters = ref<RasterAsset[]>([])
const loading = ref(false)
const selectedColormap = ref<Record<string, string>>({})
const colormaps = ['viridis', 'terrain', 'rainbow', 'plasma', 'inferno']

async function fetchRasters() {
  loading.value = true
  try {
    rasters.value = await rasterApi.list()
  } finally {
    loading.value = false
  }
}

function statusType(status: string) {
  const map: Record<string, string> = {
    ready: 'success',
    processing: 'warning',
    pending: 'info',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function loadToMap(raster: RasterAsset) {
  if (!raster.cog_path || !props.mapViewRef) return
  const cogFilename = raster.cog_path.split('/').pop()
  const colormap = selectedColormap.value[raster.id] || 'viridis'
  const titilerBase = import.meta.env.VITE_TITILER_URL || 'http://localhost:8080'
  const url = `${titilerBase}/cog/tiles/{z}/{x}/{y}.png?url=/data/processed/${cogFilename}&colormap_name=${colormap}`
  props.mapViewRef.addRasterLayer(url, raster.filename)
}

onMounted(fetchRasters)
</script>

<style scoped>
.layer-panel {
  padding: 12px;
}

.panel-actions {
  margin-bottom: 12px;
}

.raster-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
  border: 1px solid #e0e0e0;
}

.raster-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.raster-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

.raster-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
