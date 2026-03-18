<template>
  <div class="report-panel">
    <p class="section-title">生成分析报告</p>

    <el-form label-position="top" size="small">
      <el-form-item label="报告标题">
        <el-input v-model="reportTitle" placeholder="山西省 WebGIS 数据分析报告" />
      </el-form-item>

      <el-form-item label="关联栅格 (可选)">
        <el-select v-model="selectedRasterId" placeholder="选择栅格" clearable style="width: 100%">
          <el-option
            v-for="r in rasters"
            :key="r.id"
            :label="r.filename"
            :value="r.id"
          />
        </el-select>
      </el-form-item>

      <el-button type="primary" :loading="generating" @click="generateReport" style="width: 100%">
        生成报告
      </el-button>
    </el-form>

    <div v-if="currentReport" class="report-result">
      <el-divider />
      <div v-if="!currentReport.file_path">
        <el-tag type="warning">报告生成中...</el-tag>
        <el-button size="small" @click="pollStatus" :loading="polling" style="margin-left: 8px">刷新状态</el-button>
      </div>
      <div v-else>
        <el-tag type="success">报告已生成</el-tag>
        <br />
        <el-button type="primary" size="small" style="margin-top: 8px" :href="downloadUrl" tag="a" target="_blank">
          下载报告 PDF
        </el-button>
      </div>
    </div>

    <el-divider />

    <div class="report-list-header">
      <span class="section-title">历史报告</span>
      <el-button size="small" @click="fetchReports" :loading="loadingReports">刷新</el-button>
    </div>

    <el-empty v-if="reports.length === 0 && !loadingReports" description="暂无历史报告" />

    <div v-for="r in reports" :key="r.id" class="report-item">
      <div class="report-item-header">
        <span class="report-title-text">{{ r.title }}</span>
        <el-tag v-if="r.file_path" type="success" size="small">已完成</el-tag>
        <el-tag v-else type="warning" size="small">生成中</el-tag>
      </div>
      <div class="report-item-time">{{ formatTime(r.created_at) }}</div>
      <el-button
        v-if="r.file_path"
        size="small"
        type="primary"
        plain
        style="margin-top: 4px"
        :href="reportApi.downloadUrl(r.id)"
        tag="a"
        target="_blank"
      >
        下载 PDF
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { RasterAsset, Report } from '../types'
import { rasterApi } from '../api/rasterApi'
import { reportApi } from '../api/reportApi'
import { apiClient } from '../api'

const rasters = ref<RasterAsset[]>([])
const reports = ref<Report[]>([])
const reportTitle = ref('山西省 WebGIS 数据分析报告')
const selectedRasterId = ref<string | undefined>()
const generating = ref(false)
const loadingReports = ref(false)
const currentReport = ref<Report | null>(null)
const downloadUrl = ref('')
const polling = ref(false)

async function fetchRasters() {
  rasters.value = await rasterApi.list()
}

async function fetchReports() {
  loadingReports.value = true
  try {
    reports.value = await reportApi.list()
  } finally {
    loadingReports.value = false
  }
}

async function generateReport() {
  generating.value = true
  try {
    currentReport.value = await reportApi.generate({ title: reportTitle.value, raster_id: selectedRasterId.value })
    downloadUrl.value = reportApi.downloadUrl(currentReport.value.id)
    reports.value.unshift(currentReport.value)
    if (!currentReport.value.file_path) {
      setTimeout(pollStatus, 3000)
    }
  } finally {
    generating.value = false
  }
}

async function pollStatus() {
  if (!currentReport.value) return
  polling.value = true
  try {
    const res = await apiClient.get<Report>(`/api/reports/${currentReport.value.id}/download`, {
      validateStatus: (s) => s < 500,
    })
    if (res.status === 200) {
      currentReport.value.file_path = 'ready'
      const idx = reports.value.findIndex((r) => r.id === currentReport.value!.id)
      if (idx !== -1) reports.value[idx] = { ...reports.value[idx], file_path: 'ready' }
    } else {
      setTimeout(pollStatus, 3000)
    }
  } finally {
    polling.value = false
  }
}

function formatTime(timeStr: string) {
  try {
    return new Date(timeStr).toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

onMounted(() => {
  fetchRasters()
  fetchReports()
})
</script>

<style scoped>
.report-panel {
  padding: 12px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 12px;
  font-size: 13px;
  display: block;
}

.report-result {
  margin-top: 8px;
}

.report-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.report-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 6px;
  border: 1px solid #e0e0e0;
}

.report-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.report-title-text {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.report-item-time {
  font-size: 10px;
  color: #aaa;
}
</style>
