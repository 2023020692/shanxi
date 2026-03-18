<template>
  <div class="data-layer-panel">
    <!-- ===== TIF Data Section ===== -->
    <div class="section-header">
      <el-icon><DataLine /></el-icon>
      <span>TIF 数据管理</span>
    </div>

    <div class="upload-area">
      <input ref="tifInput" type="file" accept=".tif,.tiff" style="display:none" @change="handleTifUpload" />
      <el-button type="primary" size="small" @click="tifInput?.click()" :loading="uploading">
        上传 TIF 数据
      </el-button>
      <el-button size="small" @click="fetchRasters" :loading="loadingRasters">刷新</el-button>
    </div>
    <el-progress v-if="uploadProgress > 0 && uploadProgress < 100" :percentage="uploadProgress" style="margin-bottom:8px" />

    <el-empty v-if="rasters.length === 0 && !loadingRasters" description="暂无TIF数据" :image-size="50" />

    <div v-for="raster in rasters" :key="raster.id" class="raster-item">
      <div class="raster-info">
        <span class="raster-name" :title="raster.filename">{{ raster.filename }}</span>
        <el-tag :type="statusType(raster.status)" size="small">{{ statusLabel(raster.status) }}</el-tag>
      </div>
      <div class="raster-meta" v-if="raster.crs || raster.band_count">
        <span v-if="raster.crs">{{ raster.crs }}</span>
        <span v-if="raster.band_count">{{ raster.band_count }}波段</span>
      </div>

      <div v-if="raster.status === 'pending'" class="raster-controls">
        <el-button size="small" type="warning" @click="preprocessRaster(raster)">启动预处理</el-button>
      </div>

      <div v-if="raster.status === 'ready'" class="raster-controls">
        <el-select v-model="selectedColormap[raster.id]" size="small" placeholder="色带" style="width:110px">
          <el-option v-for="c in colormaps" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-button size="small" type="success" @click="loadToMap(raster)">加载地图</el-button>
        <el-button size="small" @click="openCrossValidate(raster)">交叉验证</el-button>
      </div>

      <!-- Cross-validation inline panel -->
      <div v-if="crossValidateTarget?.id === raster.id" class="cross-validate-panel">
        <p class="cv-title">选择参考数据集：</p>
        <el-select v-model="selectedRefDataset" size="small" placeholder="参考数据集" style="width:100%;margin-bottom:8px">
          <el-option
            v-for="ds in REFERENCE_DATASETS"
            :key="ds.key"
            :label="ds.name"
            :value="ds.key"
          />
        </el-select>
        <el-button
          type="primary"
          size="small"
          :loading="validating"
          :disabled="!selectedRefDataset"
          @click="runCrossValidation"
        >
          运行交叉验证
        </el-button>
        <el-button size="small" @click="crossValidateTarget = null">取消</el-button>

        <!-- Validation Results -->
        <div v-if="cvResult" class="cv-result">
          <el-divider style="margin: 8px 0" />
          <p class="cv-result-title">验证结果</p>
          <div class="cv-stats">
            <div class="cv-stat">
              <span class="cv-stat-label">R 值</span>
              <span class="cv-stat-value" :class="rValueClass(cvResult.r_value)">
                {{ cvResult.r_value.toFixed(4) }}
              </span>
            </div>
            <div class="cv-stat">
              <span class="cv-stat-label">R²</span>
              <span class="cv-stat-value">{{ cvResult.r_squared.toFixed(4) }}</span>
            </div>
            <div class="cv-stat">
              <span class="cv-stat-label">RMSE</span>
              <span class="cv-stat-value">{{ cvResult.rmse.toFixed(4) }}</span>
            </div>
            <div class="cv-stat">
              <span class="cv-stat-label">样本数</span>
              <span class="cv-stat-value">{{ cvResult.sample_count }}</span>
            </div>
          </div>
          <p class="cv-message">{{ cvResult.message }}</p>
        </div>
      </div>
    </div>

    <el-divider />

    <!-- ===== Well Point Section ===== -->
    <div class="section-header">
      <el-icon><Location /></el-icon>
      <span>煤矿井点数据</span>
    </div>

    <div class="well-actions">
      <input ref="wellFileInput" type="file" accept=".xlsx" style="display:none" @change="handleWellImport" />
      <el-button type="primary" size="small" @click="wellFileInput?.click()" :loading="importingWells">
        导入 Excel
      </el-button>
      <el-button type="success" size="small" @click="showWells" :loading="loadingWells">显示井点</el-button>
    </div>
    <p class="hint">Excel需含: name(井名)、lon(经度)、lat(纬度) 列</p>

    <el-alert v-if="wellImportMsg" :title="wellImportMsg" type="success" :closable="false" size="small" style="margin-top:6px" />
    <el-alert v-if="wellImportError" :title="wellImportError" type="error" :closable="false" size="small" style="margin-top:6px" />
    <p v-if="wellCount !== null" class="well-count">已加载 {{ wellCount }} 个井点</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { DataLine, Location } from '@element-plus/icons-vue'
import type { RasterAsset, CrossValidateResult } from '../types'
import { rasterApi } from '../api/rasterApi'
import { wellApi } from '../api/wellApi'
import { crossValidateApi, REFERENCE_DATASETS } from '../api/crossValidateApi'

const props = defineProps<{
  mapViewRef: {
    addRasterLayer: (url: string, name: string) => void
    loadWells: () => Promise<void>
  } | null
}>()

// ---- TIF Data ----
const tifInput = ref<HTMLInputElement | null>(null)
const rasters = ref<RasterAsset[]>([])
const loadingRasters = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const selectedColormap = ref<Record<string, string>>({})

const colormaps = [
  { value: 'viridis', label: 'Viridis' },
  { value: 'terrain', label: 'Terrain' },
  { value: 'rainbow', label: 'Rainbow' },
  { value: 'plasma', label: 'Plasma' },
  { value: 'inferno', label: 'Inferno' },
  { value: 'hot', label: 'Hot' },
  { value: 'jet', label: 'Jet' },
  { value: 'RdYlGn', label: 'RdYlGn' },
]

// ---- Cross Validation ----
const crossValidateTarget = ref<RasterAsset | null>(null)
const selectedRefDataset = ref('')
const validating = ref(false)
const cvResult = ref<CrossValidateResult | null>(null)

// ---- Wells ----
const wellFileInput = ref<HTMLInputElement | null>(null)
const importingWells = ref(false)
const wellImportMsg = ref('')
const wellImportError = ref('')
const loadingWells = ref(false)
const wellCount = ref<number | null>(null)

async function fetchRasters() {
  loadingRasters.value = true
  try {
    rasters.value = await rasterApi.list()
  } finally {
    loadingRasters.value = false
  }
}

async function handleTifUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  uploading.value = true
  uploadProgress.value = 10
  try {
    const raster = await rasterApi.upload(file)
    uploadProgress.value = 80
    rasters.value.unshift(raster)
    uploadProgress.value = 100
    setTimeout(() => (uploadProgress.value = 0), 1000)
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function preprocessRaster(raster: RasterAsset) {
  await rasterApi.preprocess(raster.id)
  raster.status = 'processing'
  setTimeout(fetchRasters, 3000)
}

function statusType(status: string) {
  return { ready: 'success', processing: 'warning', pending: 'info', failed: 'danger' }[status] || 'info'
}

function statusLabel(status: string) {
  return { ready: '就绪', processing: '处理中', pending: '待处理', failed: '失败' }[status] || status
}

function loadToMap(raster: RasterAsset) {
  if (!raster.cog_path || !props.mapViewRef) return
  const cogFilename = raster.cog_path.split('/').pop()
  const colormap = selectedColormap.value[raster.id] || 'viridis'
  const titilerBase = import.meta.env.VITE_TITILER_URL || 'http://localhost:8080'
  const url = `${titilerBase}/cog/tiles/{z}/{x}/{y}.png?url=/data/processed/${cogFilename}&colormap_name=${colormap}`
  props.mapViewRef.addRasterLayer(url, raster.filename)
}

function openCrossValidate(raster: RasterAsset) {
  crossValidateTarget.value = raster
  selectedRefDataset.value = ''
  cvResult.value = null
}

async function runCrossValidation() {
  if (!crossValidateTarget.value || !selectedRefDataset.value) return
  validating.value = true
  cvResult.value = null
  try {
    cvResult.value = await crossValidateApi.validate(
      crossValidateTarget.value.id,
      selectedRefDataset.value,
    )
  } finally {
    validating.value = false
  }
}

function rValueClass(r: number) {
  if (r >= 0.9) return 'r-excellent'
  if (r >= 0.75) return 'r-good'
  if (r >= 0.6) return 'r-fair'
  return 'r-poor'
}

// ---- Well Methods ----
async function handleWellImport(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  importingWells.value = true
  wellImportMsg.value = ''
  wellImportError.value = ''
  try {
    const res = await wellApi.importExcel(file)
    wellImportMsg.value = `成功导入 ${res.imported} 个井点`
  } catch (e: unknown) {
    wellImportError.value =
      (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '导入失败'
  } finally {
    importingWells.value = false
    input.value = ''
  }
}

async function showWells() {
  if (!props.mapViewRef) return
  loadingWells.value = true
  try {
    await props.mapViewRef.loadWells()
    const data = await wellApi.list()
    wellCount.value = data.features.length
  } finally {
    loadingWells.value = false
  }
}

onMounted(fetchRasters)
</script>

<style scoped>
.data-layer-panel {
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
  margin-bottom: 8px;
}

.upload-area {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.raster-item {
  background: #1e2d4a;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
  border: 1px solid #2c3e5a;
}

.raster-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.raster-name {
  font-size: 12px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
  color: #ccc;
}

.raster-meta {
  font-size: 11px;
  color: #888;
  margin-bottom: 6px;
  display: flex;
  gap: 8px;
}

.raster-controls {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.cross-validate-panel {
  margin-top: 10px;
  padding: 10px;
  background: #13213a;
  border-radius: 6px;
}

.cv-title {
  font-size: 12px;
  color: #aaa;
  margin-bottom: 6px;
}

.cv-result-title {
  font-size: 12px;
  font-weight: bold;
  color: #64b5f6;
  margin-bottom: 6px;
}

.cv-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 6px;
}

.cv-stat {
  background: #1a2a42;
  border-radius: 4px;
  padding: 6px;
  text-align: center;
}

.cv-stat-label {
  display: block;
  font-size: 10px;
  color: #888;
}

.cv-stat-value {
  display: block;
  font-size: 15px;
  font-weight: bold;
  color: #fff;
}

.r-excellent { color: #4caf50 !important; }
.r-good { color: #8bc34a !important; }
.r-fair { color: #ffc107 !important; }
.r-poor { color: #f44336 !important; }

.cv-message {
  font-size: 11px;
  color: #90caf9;
  word-break: break-all;
}

.well-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.hint {
  font-size: 11px;
  color: #777;
  margin-bottom: 6px;
}

.well-count {
  color: #67c23a;
  font-size: 12px;
  margin-top: 6px;
}
</style>
