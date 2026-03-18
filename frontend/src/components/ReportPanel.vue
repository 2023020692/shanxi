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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { RasterAsset, Report } from '../types'
import { rasterApi } from '../api/rasterApi'
import { reportApi } from '../api/reportApi'
import { apiClient } from '../api'

const rasters = ref<RasterAsset[]>([])
const reportTitle = ref('山西省 WebGIS 数据分析报告')
const selectedRasterId = ref<string | undefined>()
const generating = ref(false)
const currentReport = ref<Report | null>(null)
const downloadUrl = ref('')
const polling = ref(false)

async function fetchRasters() {
  rasters.value = await rasterApi.list()
}

async function generateReport() {
  generating.value = true
  try {
    currentReport.value = await reportApi.generate(reportTitle.value, selectedRasterId.value)
    downloadUrl.value = reportApi.downloadUrl(currentReport.value.id)
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
    } else {
      setTimeout(pollStatus, 3000)
    }
  } finally {
    polling.value = false
  }
}

onMounted(fetchRasters)
</script>

<style scoped>
.report-panel {
  padding: 12px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 12px;
}

.report-result {
  margin-top: 8px;
}
</style>
