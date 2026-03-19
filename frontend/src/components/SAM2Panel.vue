<template>
  <div class="sam2-panel">
    <div class="section-header">
      <el-icon><Cpu /></el-icon>
      <span>SAM2 分析</span>
      <el-tag type="info" size="small" style="margin-left:auto">SAM2 v2.1</el-tag>
    </div>

    <!-- ──────── Section 1: PNG/JPG Satellite Image Analysis ──────── -->
    <div class="sub-section">
      <p class="sub-title">
        <el-icon><PictureFilled /></el-icon>
        卫星图像分析（PNG / JPG）
      </p>
      <p class="description">上传卫星图像，系统将自动分析并添加到分析列表，可点击图像放大查看。</p>

      <div class="upload-zone" @click="imgInput?.click()" @dragover.prevent @drop.prevent="onImgDrop">
        <input ref="imgInput" type="file" accept=".png,.jpg,.jpeg" style="display:none" @change="onImgChange" />
        <el-icon class="upload-icon"><Upload /></el-icon>
        <p class="upload-text">点击或拖拽上传 PNG / JPG 图像</p>
        <p v-if="selectedImgFile" class="selected-file">
          <el-icon><Document /></el-icon>
          {{ selectedImgFile.name }} ({{ formatSize(selectedImgFile.size) }})
        </p>
      </div>

      <el-button
        type="primary"
        :disabled="!selectedImgFile"
        :loading="analyzingImg"
        @click="runImageAnalysis"
        style="width:100%;margin-top:8px"
      >
        {{ analyzingImg ? '分析中...' : '分析卫星图像' }}
      </el-button>

      <!-- Satellite Image List -->
      <div class="list-header" style="margin-top:12px">
        <span class="list-title">卫星图像列表</span>
        <el-button size="small" text type="primary" :loading="loadingImages" @click="loadSatelliteImages">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>

      <div v-if="satelliteImages.length === 0" class="empty-tip">暂无分析结果</div>
      <div v-else class="image-list">
        <div
          v-for="img in satelliteImages"
          :key="img.image_id"
          class="image-item"
          @click="viewImage(img)"
        >
          <div class="image-thumb-wrap">
            <!-- Show satellite-2 image if available, else satellite-1 -->
            <img
              :src="img.satellite2_url || img.image_url"
              class="image-thumb"
              :alt="img.filename"
              @error="onImgError"
            />
            <div class="image-overlay">
              <el-icon><ZoomIn /></el-icon>
            </div>
          </div>
          <div class="image-info">
            <span class="image-filename" :title="img.filename">{{ img.filename }}</span>
            <span class="image-meta">{{ formatDate(img.created_at) }}</span>
            <el-tag type="success" size="small">{{ img.message }}</el-tag>
            <el-tag v-if="img.satellite2_url" type="info" size="small" style="margin-top:2px">卫星2</el-tag>
          </div>
        </div>
      </div>
    </div>

    <el-divider style="margin:14px 0" />

    <!-- ──────── Section 2: TIF Heatmap Analysis ──────── -->
    <div class="sub-section">
      <p class="sub-title">
        <el-icon><Grid /></el-icon>
        TIF 热力图分析
      </p>
      <p class="description">上传TIF图像，SAM2将生成热力图数据，可渲染到地图。</p>

      <div class="upload-zone" @click="tifInput?.click()" @dragover.prevent @drop.prevent="onTifDrop">
        <input ref="tifInput" type="file" accept=".tif,.tiff" style="display:none" @change="onTifChange" />
        <el-icon class="upload-icon"><Upload /></el-icon>
        <p class="upload-text">点击或拖拽上传 TIF / TIFF 文件</p>
        <p v-if="selectedTifFile" class="selected-file">
          <el-icon><Document /></el-icon>
          {{ selectedTifFile.name }} ({{ formatSize(selectedTifFile.size) }})
        </p>
      </div>

      <el-button
        type="warning"
        :disabled="!selectedTifFile"
        :loading="analyzingTif"
        @click="runTifAnalysis"
        style="width:100%;margin-top:8px"
      >
        {{ analyzingTif ? 'SAM2分析中（约10秒）...' : '启动 TIF 热力图分析' }}
      </el-button>

      <!-- SAM2 Raster List -->
      <div class="list-header" style="margin-top:12px">
        <span class="list-title">SAM2 栅格列表</span>
        <el-button size="small" text type="primary" :loading="loadingRasters" @click="loadSAM2Rasters">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>

      <div v-if="sam2Rasters.length === 0" class="empty-tip">暂无栅格分析结果</div>
      <div v-else class="raster-list">
        <div
          v-for="raster in sam2Rasters"
          :key="raster.raster_id"
          class="raster-item"
        >
          <div class="raster-info">
            <span class="raster-filename" :title="raster.filename">{{ raster.filename }}</span>
            <span class="raster-meta">{{ formatDate(raster.created_at) }}</span>
          </div>
          <div class="raster-actions">
            <el-select
              v-model="rasterColormaps[raster.raster_id]"
              size="small"
              style="width:76px"
              placeholder="Hot"
            >
              <el-option value="hot" label="Hot" />
              <el-option value="plasma" label="Plasma" />
              <el-option value="inferno" label="Inferno" />
              <el-option value="viridis" label="Viridis" />
            </el-select>
            <el-button
              size="small"
              :type="activeRasterId === raster.raster_id ? 'danger' : 'success'"
              @click="toggleRasterHeatmap(raster)"
            >
              {{ activeRasterId === raster.raster_id ? '取消渲染' : '渲染热力图' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Image Preview Dialog -->
    <el-dialog
      v-model="previewVisible"
      :title="previewImage?.filename"
      width="80%"
      :append-to-body="true"
      class="image-preview-dialog"
    >
      <div class="preview-container">
        <img
          v-if="previewImage"
          :src="previewImage.satellite2_url || previewImage.image_url"
          class="preview-img"
          :alt="previewImage?.filename"
        />
      </div>
      <template v-if="previewImage?.satellite2_url" #footer>
        <span style="font-size:12px;color:#90caf9">路径已转换为卫星2存放目录</span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Cpu, Upload, Document, Refresh, ZoomIn, PictureFilled, Grid } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { SatelliteImage, SAM2Raster } from '../types'
import { sam2Api } from '../api/sam2Api'

const props = defineProps<{
  mapViewRef: {
    showSAM2Heatmap: (
      grid: Array<{ lon: number; lat: number; intensity: number }>,
      colormap: string,
    ) => void
    renderTifLayer: (tifUrl: string, colormap: string, title: string) => Promise<void>
    clearTifLayer: () => void
  } | null
}>()

// ── PNG/JPG section ──
const imgInput = ref<HTMLInputElement | null>(null)
const selectedImgFile = ref<File | null>(null)
const analyzingImg = ref(false)
const satelliteImages = ref<SatelliteImage[]>([])
const loadingImages = ref(false)

// ── TIF section ──
const tifInput = ref<HTMLInputElement | null>(null)
const selectedTifFile = ref<File | null>(null)
const analyzingTif = ref(false)
const sam2Rasters = ref<SAM2Raster[]>([])
const loadingRasters = ref(false)
const rasterColormaps = ref<Record<string, string>>({})
const activeRasterId = ref<string | null>(null)

// ── Image preview ──
const previewVisible = ref(false)
const previewImage = ref<SatelliteImage | null>(null)

function onImgChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) selectedImgFile.value = input.files[0]
}

function onImgDrop(event: DragEvent) {
  const files = event.dataTransfer?.files
  if (files?.length) selectedImgFile.value = files[0]
}

function onTifChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) selectedTifFile.value = input.files[0]
}

function onTifDrop(event: DragEvent) {
  const files = event.dataTransfer?.files
  if (files?.length) selectedTifFile.value = files[0]
}

async function runImageAnalysis() {
  if (!selectedImgFile.value) return
  analyzingImg.value = true
  try {
    const result = await sam2Api.analyzeImage(selectedImgFile.value)
    ElMessage.success('分析成功，卫星图像已添加到列表')
    // result.satellite2_url is populated by the backend after satellite-1 analysis
    satelliteImages.value.unshift(result)
    selectedImgFile.value = null
    if (imgInput.value) imgInput.value.value = ''
  } catch {
    ElMessage.error('分析失败，请重试')
  } finally {
    analyzingImg.value = false
  }
}

async function runTifAnalysis() {
  if (!selectedTifFile.value) return
  analyzingTif.value = true
  try {
    const result = await sam2Api.analyzeTif(selectedTifFile.value)
    ElMessage.success('TIF热力图分析完成')
    rasterColormaps.value[result.raster_id] = 'hot'
    sam2Rasters.value.unshift(result)
    selectedTifFile.value = null
    if (tifInput.value) tifInput.value.value = ''
    // Auto-render the new result
    toggleRasterHeatmap(result)
  } catch {
    ElMessage.error('TIF分析失败，请重试')
  } finally {
    analyzingTif.value = false
  }
}

async function loadSatelliteImages() {
  loadingImages.value = true
  try {
    satelliteImages.value = await sam2Api.listSatelliteImages()
  } catch {
    // silently ignore
  } finally {
    loadingImages.value = false
  }
}

async function loadSAM2Rasters() {
  loadingRasters.value = true
  try {
    sam2Rasters.value = await sam2Api.listSAM2Rasters()
    for (const r of sam2Rasters.value) {
      if (!rasterColormaps.value[r.raster_id]) {
        rasterColormaps.value[r.raster_id] = 'hot'
      }
    }
  } catch {
    // silently ignore
  } finally {
    loadingRasters.value = false
  }
}

async function toggleRasterHeatmap(raster: SAM2Raster) {
  if (!props.mapViewRef) return
  if (activeRasterId.value === raster.raster_id) {
    // Cancel render
    if (raster.tif_url) {
      props.mapViewRef.clearTifLayer()
    } else {
      props.mapViewRef.showSAM2Heatmap([], 'hot')
    }
    activeRasterId.value = null
    ElMessage.info('已取消热力图渲染')
  } else {
    const colormap = rasterColormaps.value[raster.raster_id] || 'hot'
    // Prefer geotiff.js + Deck.gl WebGL rendering when TIF URL is available
    if (raster.tif_url) {
      try {
        await props.mapViewRef.renderTifLayer(raster.tif_url, colormap, `${raster.filename} - SAM2热力图`)
        activeRasterId.value = raster.raster_id
        ElMessage.success(`"${raster.filename}" TIF已通过WebGL渲染到地图`)
        return
      } catch {
        // Fall through to grid-based rendering
      }
    }
    // Fall back to grid-point heatmap
    props.mapViewRef.showSAM2Heatmap(raster.heatmap_grid, colormap)
    activeRasterId.value = raster.raster_id
    ElMessage.success(`"${raster.filename}" 热力图已渲染到地图`)
  }
}

function viewImage(img: SatelliteImage) {
  previewImage.value = img
  previewVisible.value = true
}

function onImgError(event: Event) {
  const target = event.target as HTMLImageElement
  target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60"><rect width="60" height="60" fill="%23334"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%23888" font-size="10">无图</text></svg>'
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(dateStr?: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadSatelliteImages()
  loadSAM2Rasters()
})
</script>

<style scoped>
.sam2-panel {
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

.sub-section {
  margin-bottom: 4px;
}

.sub-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: bold;
  font-size: 12px;
  color: #90caf9;
  margin-bottom: 6px;
}

.description {
  font-size: 11px;
  color: #777;
  margin-bottom: 10px;
  line-height: 1.5;
}

.upload-zone {
  border: 2px dashed #2c3e5a;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-zone:hover {
  border-color: #409eff;
}

.upload-icon {
  font-size: 28px;
  color: #555;
  margin-bottom: 6px;
}

.upload-text {
  color: #ccc;
  font-size: 12px;
  margin-bottom: 4px;
}

.selected-file {
  margin-top: 6px;
  font-size: 11px;
  color: #64b5f6;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.list-title {
  font-size: 12px;
  font-weight: bold;
  color: #e0e0e0;
}

.empty-tip {
  font-size: 12px;
  color: #555;
  text-align: center;
  padding: 12px 0;
}

/* ── Satellite image list ── */
.image-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.image-item {
  display: flex;
  gap: 10px;
  background: #13213a;
  border-radius: 6px;
  padding: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.image-item:hover {
  background: #1a2d4a;
}

.image-thumb-wrap {
  position: relative;
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
}

.image-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.image-filename {
  font-size: 12px;
  font-weight: 500;
  color: #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-meta {
  font-size: 11px;
  color: #666;
}

/* ── Raster list ── */
.raster-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.raster-item {
  background: #13213a;
  border-radius: 6px;
  padding: 8px 10px;
}

.raster-info {
  margin-bottom: 6px;
}

.raster-filename {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.raster-meta {
  display: block;
  font-size: 11px;
  color: #666;
  margin-top: 2px;
}

.raster-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

/* ── Preview dialog ── */
.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  background: #0a1628;
  border-radius: 6px;
}

.preview-img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 4px;
}
</style>
