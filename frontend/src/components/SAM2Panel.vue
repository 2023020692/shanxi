<template>
  <div class="sam2-panel">
    <div class="section-header">
      <el-icon><Cpu /></el-icon>
      <span>SAM2 目标识别</span>
      <el-tag type="info" size="small" style="margin-left:auto">SAM2 v2.1</el-tag>
    </div>

    <p class="description">
      上传带有煤矿井点标注的卫星图像，SAM2模型将自动识别目标区域并输出热力图覆盖层。
    </p>

    <!-- Upload Area -->
    <div class="upload-zone" @click="fileInput?.click()" @dragover.prevent @drop.prevent="onDrop">
      <input ref="fileInput" type="file" accept=".png,.jpg,.jpeg,.tif,.tiff" style="display:none" @change="onFileChange" />
      <el-icon class="upload-icon"><Upload /></el-icon>
      <p class="upload-text">点击或拖拽上传卫星图像</p>
      <p class="upload-hint">支持 PNG / JPG / TIF 格式</p>
      <p v-if="selectedFile" class="selected-file">
        <el-icon><Document /></el-icon>
        {{ selectedFile.name }} ({{ formatSize(selectedFile.size) }})
      </p>
    </div>

    <el-button
      type="primary"
      :disabled="!selectedFile"
      :loading="detecting"
      @click="runDetection"
      style="width:100%;margin-top:10px"
    >
      启动 SAM2 目标识别
    </el-button>

    <!-- Current Run Result -->
    <div v-if="result" class="result-section">
      <el-divider />
      <div class="result-header-row">
        <span class="result-title">识别结果</span>
        <el-tag :type="result.status === 'completed' ? 'success' : 'warning'" size="small">
          {{ result.status === 'completed' ? '识别完成' : '就绪' }}
        </el-tag>
      </div>

      <div v-if="result.detection_count > 0" class="detection-summary">
        <div class="summary-stat">
          <span class="s-val">{{ result.detection_count }}</span>
          <span class="s-lbl">识别目标数</span>
        </div>
        <div class="summary-stat">
          <span class="s-val">{{ result.filename || '—' }}</span>
          <span class="s-lbl">图像文件</span>
        </div>
        <div class="summary-stat">
          <span class="s-val">{{ result.heatmap_grid.length }}</span>
          <span class="s-lbl">热力图格点</span>
        </div>
      </div>

      <p class="result-message">{{ result.message }}</p>

      <!-- Detection list -->
      <div v-if="result.detections.length > 0" class="detection-list">
        <p class="det-list-title">检测边界框（前5个）：</p>
        <div
          v-for="(d, idx) in result.detections.slice(0, 5)"
          :key="idx"
          class="det-item"
        >
          <span class="det-idx">#{{ idx + 1 }}</span>
          <span class="det-label">{{ d.label }}</span>
          <el-progress
            :percentage="Math.round(d.confidence * 100)"
            :stroke-width="8"
            :color="confidenceColor(d.confidence)"
            style="flex:1;margin: 0 8px"
          />
          <span class="det-conf">{{ (d.confidence * 100).toFixed(1) }}%</span>
        </div>
      </div>

      <!-- Heatmap controls -->
      <div v-if="result.heatmap_grid.length > 0" class="heatmap-controls">
        <el-divider style="margin:8px 0" />
        <p class="heatmap-title">热力图渲染</p>
        <div class="heatmap-row">
          <el-select v-model="heatmapColormap" size="small" style="width:100px">
            <el-option value="hot" label="Hot" />
            <el-option value="plasma" label="Plasma" />
            <el-option value="inferno" label="Inferno" />
            <el-option value="viridis" label="Viridis" />
          </el-select>
          <el-button size="small" type="success" @click="renderHeatmapToMap(result!)">
            渲染热力图到地图
          </el-button>
        </div>
      </div>
    </div>

    <!-- ── Historical Results List ── -->
    <el-divider style="margin:14px 0 8px">
      <span class="history-divider-label">
        <el-icon><List /></el-icon>
        历史识别结果
      </span>
    </el-divider>

    <div class="history-refresh-row">
      <span class="history-count">共 {{ allResults.length }} 条记录</span>
      <el-button size="small" :loading="loadingHistory" @click="loadHistory" text type="primary">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-tabs v-model="activeHistoryTab" class="history-tabs" size="small">
      <!-- Tab 1: Heatmap List -->
      <el-tab-pane name="heatmap">
        <template #label>
          <span class="tab-label">
            <el-icon><HeatMap /></el-icon>
            热力图列表
          </span>
        </template>

        <div v-if="heatmapResults.length === 0" class="empty-tip">暂无热力图数据</div>
        <div v-else class="history-list">
          <div
            v-for="item in heatmapResults"
            :key="item.detection_id"
            class="history-item"
          >
            <div class="hi-info">
              <span class="hi-filename" :title="item.filename">{{ item.filename }}</span>
              <span class="hi-meta">
                {{ item.heatmap_grid.length }} 格点 · {{ formatDate(item.created_at) }}
              </span>
            </div>
            <div class="hi-actions">
              <el-select
                v-model="colormapMap[item.detection_id]"
                size="small"
                style="width:76px"
                placeholder="Hot"
                @click.stop
              >
                <el-option value="hot" label="Hot" />
                <el-option value="plasma" label="Plasma" />
                <el-option value="inferno" label="Inferno" />
                <el-option value="viridis" label="Viridis" />
              </el-select>
              <el-button
                size="small"
                type="success"
                @click="renderHeatmapToMap(item)"
              >渲染</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: Satellite Target Detection Results List -->
      <el-tab-pane name="detection">
        <template #label>
          <span class="tab-label">
            <el-icon><Aim /></el-icon>
            卫星目标识别结果
          </span>
        </template>

        <div v-if="detectionResults.length === 0" class="empty-tip">暂无目标识别结果</div>
        <div v-else class="history-list">
          <div
            v-for="item in detectionResults"
            :key="item.detection_id"
            class="history-item history-item--detection"
          >
            <div class="hi-info">
              <span class="hi-filename" :title="item.filename">{{ item.filename }}</span>
              <span class="hi-meta">
                识别到 <strong style="color:#90caf9">{{ item.detection_count }}</strong> 个目标
                · {{ formatDate(item.created_at) }}
              </span>
            </div>
            <!-- Top-3 detections inline -->
            <div class="inline-dets">
              <div
                v-for="(d, i) in item.detections.slice(0, 3)"
                :key="i"
                class="inline-det"
              >
                <span class="inline-det-label">{{ d.label }}</span>
                <el-progress
                  :percentage="Math.round(d.confidence * 100)"
                  :stroke-width="5"
                  :color="confidenceColor(d.confidence)"
                  style="flex:1;margin:0 6px"
                />
                <span class="inline-det-conf">{{ (d.confidence * 100).toFixed(0) }}%</span>
              </div>
              <p v-if="item.detections.length > 3" class="more-tip">
                +{{ item.detections.length - 3 }} 个目标未展示
              </p>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Cpu, Upload, Document, List, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { SAM2Result } from '../types'
import { sam2Api } from '../api/sam2Api'

// Custom icon components (inline SVG wrappers for icons not in Element-Plus icon set)
const HeatMap = {
  render() {
    return h('svg', { viewBox: '0 0 1024 1024', width: '1em', height: '1em', fill: 'currentColor' }, [
      h('path', { d: 'M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z' }),
    ])
  },
}
const Aim = {
  render() {
    return h('svg', { viewBox: '0 0 1024 1024', width: '1em', height: '1em', fill: 'currentColor' }, [
      h('path', { d: 'M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372zm0-550c-98.2 0-178 79.8-178 178s79.8 178 178 178 178-79.8 178-178-79.8-178-178-178zm0 280c-56.2 0-102-45.8-102-102s45.8-102 102-102 102 45.8 102 102-45.8 102-102 102z' }),
    ])
  },
}

import { h } from 'vue'

const props = defineProps<{
  mapViewRef: {
    showSAM2Heatmap: (
      grid: Array<{ lon: number; lat: number; intensity: number }>,
      colormap: string,
    ) => void
  } | null
  onResult?: (result: SAM2Result) => void
}>()

const emit = defineEmits<{
  (e: 'result', result: SAM2Result): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const detecting = ref(false)
const result = ref<SAM2Result | null>(null)
const heatmapColormap = ref('hot')

// History
const allResults = ref<SAM2Result[]>([])
const loadingHistory = ref(false)
const activeHistoryTab = ref('heatmap')
const colormapMap = ref<Record<string, string>>({})

const heatmapResults = computed(() =>
  allResults.value.filter((r) => r.heatmap_grid && r.heatmap_grid.length > 0),
)
const detectionResults = computed(() =>
  allResults.value.filter((r) => r.detections && r.detections.length > 0),
)

async function loadHistory() {
  loadingHistory.value = true
  try {
    allResults.value = await sam2Api.list()
    // Initialise per-item colormap defaults
    for (const r of allResults.value) {
      if (!colormapMap.value[r.detection_id]) {
        colormapMap.value[r.detection_id] = 'hot'
      }
    }
  } catch {
    // silently ignore – history is non-critical
  } finally {
    loadingHistory.value = false
  }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    selectedFile.value = input.files[0]
    result.value = null
  }
}

function onDrop(event: DragEvent) {
  const files = event.dataTransfer?.files
  if (files?.length) {
    selectedFile.value = files[0]
    result.value = null
  }
}

async function runDetection() {
  if (!selectedFile.value) return
  detecting.value = true
  result.value = null
  try {
    result.value = await sam2Api.detect(selectedFile.value)
    emit('result', result.value)
    ElMessage.success(`SAM2识别完成，发现 ${result.value.detection_count} 个目标`)
    // Refresh history to include the new result
    await loadHistory()
  } catch {
    ElMessage.error('SAM2识别失败，请重试')
  } finally {
    detecting.value = false
  }
}

function renderHeatmapToMap(item: SAM2Result) {
  if (!props.mapViewRef) return
  const colormap = item.detection_id
    ? (colormapMap.value[item.detection_id] ?? heatmapColormap.value)
    : heatmapColormap.value
  props.mapViewRef.showSAM2Heatmap(item.heatmap_grid, colormap)
  ElMessage.success('热力图已渲染到地图')
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

function confidenceColor(conf: number) {
  if (conf >= 0.9) return '#4caf50'
  if (conf >= 0.75) return '#8bc34a'
  if (conf >= 0.6) return '#ffc107'
  return '#f44336'
}

onMounted(loadHistory)
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
  margin-bottom: 8px;
}

.description {
  font-size: 12px;
  color: #888;
  margin-bottom: 12px;
  line-height: 1.5;
}

.upload-zone {
  border: 2px dashed #2c3e5a;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-zone:hover {
  border-color: #409eff;
}

.upload-icon {
  font-size: 32px;
  color: #555;
  margin-bottom: 8px;
}

.upload-text {
  color: #ccc;
  font-size: 13px;
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 11px;
  color: #666;
}

.selected-file {
  margin-top: 8px;
  font-size: 12px;
  color: #64b5f6;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.result-section {
  margin-top: 4px;
}

.result-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-title {
  font-weight: bold;
  color: #e0e0e0;
}

.detection-summary {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.summary-stat {
  flex: 1;
  background: #13213a;
  border-radius: 4px;
  padding: 6px;
  text-align: center;
}

.s-val {
  display: block;
  font-size: 15px;
  font-weight: bold;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.s-lbl {
  display: block;
  font-size: 10px;
  color: #90caf9;
}

.result-message {
  font-size: 12px;
  color: #90caf9;
  margin-bottom: 8px;
}

.detection-list {
  background: #13213a;
  border-radius: 6px;
  padding: 8px;
}

.det-list-title {
  font-size: 11px;
  color: #aaa;
  margin-bottom: 6px;
}

.det-item {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  font-size: 12px;
}

.det-idx {
  color: #666;
  width: 24px;
}

.det-label {
  color: #ccc;
  width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.det-conf {
  color: #aaa;
  width: 40px;
  text-align: right;
}

.heatmap-title {
  font-size: 12px;
  font-weight: bold;
  color: #e0e0e0;
  margin-bottom: 8px;
}

.heatmap-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* ── History section ── */

.history-divider-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #888;
}

.history-refresh-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.history-count {
  font-size: 11px;
  color: #666;
}

.history-tabs {
  --el-tabs-header-height: 32px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.empty-tip {
  font-size: 12px;
  color: #555;
  text-align: center;
  padding: 14px 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 2px;
}

.history-item {
  background: #13213a;
  border-radius: 6px;
  padding: 8px 10px;
}

.history-item--detection {
  background: #0f1e36;
  border-left: 3px solid #1565c0;
}

.hi-info {
  margin-bottom: 6px;
}

.hi-filename {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hi-meta {
  display: block;
  font-size: 11px;
  color: #666;
  margin-top: 2px;
}

.hi-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

/* Inline detections inside each history-item--detection */
.inline-dets {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.inline-det {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.inline-det-label {
  color: #aaa;
  width: 76px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inline-det-conf {
  color: #888;
  width: 32px;
  text-align: right;
}

.more-tip {
  font-size: 10px;
  color: #555;
  margin-top: 2px;
}
</style>
