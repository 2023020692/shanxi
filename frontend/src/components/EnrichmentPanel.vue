<template>
  <div class="enrichment-panel">
    <!-- Create New Analysis -->
    <div class="section-header">
      <el-icon><TrendCharts /></el-icon>
      <span>煤矿富集指数识别</span>
    </div>

    <el-form label-position="top" size="small">
      <el-form-item label="分析名称">
        <el-input v-model="form.name" placeholder="例：山西北部富集分析" />
      </el-form-item>

      <el-form-item label="选择数据图层（多选）">
        <div style="display:flex;gap:6px;width:100%">
          <el-select
            v-model="form.selectedRasterIds"
            multiple
            collapse-tags
            placeholder="选择TIF数据层"
            style="flex:1"
            :loading="loadingRasters"
          >
            <el-option
              v-for="r in readyRasters"
              :key="r.id"
              :label="r.filename"
              :value="r.id"
            />
          </el-select>
          <el-button size="small" :loading="loadingRasters" @click="fetchRasters" title="刷新数据图层列表">
            刷新
          </el-button>
        </div>
        <div v-if="readyRasters.length === 0 && !loadingRasters" class="hint">暂无TIF数据，请先在数据图层模块上传TIF文件</div>
      </el-form-item>

      <el-button
        type="primary"
        :disabled="!form.name || form.selectedRasterIds.length === 0"
        :loading="analyzing"
        @click="runAnalysis"
        style="width:100%"
      >
        开始富集指数识别
      </el-button>
    </el-form>

    <el-divider />

    <!-- Results List -->
    <div class="section-header">
      <el-icon><List /></el-icon>
      <span>识别结果列表</span>
      <el-button size="small" text @click="fetchResults" style="margin-left:auto">刷新</el-button>
    </div>

    <el-empty v-if="results.length === 0 && !loadingResults" description="暂无识别结果" :image-size="50" />

    <div v-for="item in results" :key="item.id" class="result-item">
      <div class="result-header">
        <span class="result-name">{{ item.name }}</span>
        <el-tag type="success" size="small">{{ item.method_name }}</el-tag>
      </div>

      <div class="result-stats" v-if="item.enrichment_index !== undefined">
        <div class="stat-block">
          <span class="stat-val">{{ (item.enrichment_index! * 100).toFixed(1) }}%</span>
          <span class="stat-lbl">富集指数</span>
        </div>
        <div class="stat-block">
          <span class="stat-val">{{ (item.high_value_ratio! * 100).toFixed(1) }}%</span>
          <span class="stat-lbl">高值占比</span>
        </div>
        <div class="stat-block">
          <span class="stat-val">{{ item.coverage_area_km2?.toFixed(0) }}</span>
          <span class="stat-lbl">覆盖km²</span>
        </div>
      </div>

      <div class="result-controls">
        <el-select
          v-model="selectedColormaps[item.id]"
          size="small"
          placeholder="色带"
          style="width:90px"
        >
          <el-option v-for="c in colormaps" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-button size="small" type="success" @click="renderToMap(item)">
          渲染到地图
        </el-button>
      </div>

      <div class="result-meta">
        <span>来源图层: {{ item.raster_ids.length }} 个</span>
        <span>{{ formatDate(item.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { TrendCharts, List } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { RasterAsset, EnrichmentResultItem, EnrichmentGridPoint } from '../types'
import { rasterApi } from '../api/rasterApi'
import { enrichmentApi } from '../api/enrichmentApi'

const props = defineProps<{
  mapViewRef: {
    showEnrichmentLayer: (grid: EnrichmentGridPoint[], colormap: string, name: string) => void
  } | null
}>()

const form = ref({
  name: '',
  selectedRasterIds: [] as string[],
})

const colormaps = [
  { value: 'hot', label: 'Hot' },
  { value: 'viridis', label: 'Viridis' },
  { value: 'plasma', label: 'Plasma' },
  { value: 'inferno', label: 'Inferno' },
  { value: 'RdYlGn', label: 'RdYlGn' },
  { value: 'rainbow', label: 'Rainbow' },
]

const rasters = ref<RasterAsset[]>([])
const loadingRasters = ref(false)
const analyzing = ref(false)
const results = ref<EnrichmentResultItem[]>([])
const loadingResults = ref(false)
const selectedColormaps = ref<Record<string, string>>({})

const readyRasters = computed(() => rasters.value.filter((r) => r.status === 'ready'))

async function fetchRasters() {
  loadingRasters.value = true
  try {
    rasters.value = await rasterApi.list()
  } finally {
    loadingRasters.value = false
  }
}

async function fetchResults() {
  loadingResults.value = true
  try {
    results.value = await enrichmentApi.list()
  } finally {
    loadingResults.value = false
  }
}

async function runAnalysis() {
  if (!form.value.name || form.value.selectedRasterIds.length === 0) return
  analyzing.value = true
  try {
    const result = await enrichmentApi.analyze(
      form.value.name,
      form.value.selectedRasterIds,
    )
    results.value.unshift(result)
    form.value.name = ''
    form.value.selectedRasterIds = []
    ElMessage.success('富集指数识别完成')
  } catch {
    ElMessage.error('识别分析失败，请重试')
  } finally {
    analyzing.value = false
  }
}

async function renderToMap(item: EnrichmentResultItem) {
  if (!props.mapViewRef) return
  try {
    const data = await enrichmentApi.getGrid(item.id)
    const colormap = selectedColormaps.value[item.id] || item.colormap || 'hot'
    props.mapViewRef.showEnrichmentLayer(data.grid || [], colormap, item.name)
    ElMessage.success(`"${item.name}" 已渲染到地图`)
  } catch {
    ElMessage.error('渲染失败，请重试')
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  await Promise.all([fetchRasters(), fetchResults()])
})
</script>

<style scoped>
.enrichment-panel {
  padding: 12px;
  font-size: 13px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: bold;
  font-size: 13px;
  color: #e0e0e0;
  margin-bottom: 10px;
}

.hint {
  font-size: 11px;
  color: #888;
  margin-top: 4px;
}

.result-item {
  background: #1e2d4a;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #2c3e5a;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-name {
  font-weight: bold;
  color: #e0e0e0;
  font-size: 13px;
}

.result-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.stat-block {
  flex: 1;
  background: #13213a;
  border-radius: 4px;
  padding: 6px;
  text-align: center;
}

.stat-val {
  display: block;
  font-size: 16px;
  font-weight: bold;
  color: #fff;
}

.stat-lbl {
  display: block;
  font-size: 10px;
  color: #90caf9;
}

.result-controls {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #666;
}
</style>
