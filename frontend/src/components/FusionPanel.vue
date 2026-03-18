<template>
  <div class="fusion-panel">
    <p class="section-title">创建融合任务</p>

    <el-form :model="form" label-position="top" size="small">
      <el-form-item label="任务名称">
        <el-input v-model="form.name" placeholder="输入融合任务名称" />
      </el-form-item>

      <el-form-item label="融合方法">
        <el-select v-model="form.method" style="width: 100%">
          <el-option label="叠加分析 (Overlay)" value="overlay" />
          <el-option label="加权求和 (Weighted Sum)" value="weighted_sum" />
          <el-option label="均值融合 (Mean)" value="mean" />
        </el-select>
      </el-form-item>

      <el-form-item label="选择栅格数据 (可选)">
        <el-select
          v-model="form.rasterIds"
          multiple
          placeholder="选择参与融合的栅格"
          style="width: 100%"
        >
          <el-option
            v-for="r in rasters"
            :key="r.id"
            :label="r.filename"
            :value="r.id"
          />
        </el-select>
      </el-form-item>

      <el-button
        type="primary"
        :loading="creating"
        :disabled="!form.name.trim()"
        @click="createJob"
        style="width: 100%"
      >
        创建融合任务
      </el-button>
    </el-form>

    <el-divider />

    <div class="job-list-header">
      <span class="section-title">融合任务列表</span>
      <el-button size="small" @click="fetchJobs" :loading="loadingJobs">刷新</el-button>
    </div>

    <el-empty v-if="jobs.length === 0 && !loadingJobs" description="暂无融合任务" />

    <div v-for="job in jobs" :key="job.id" class="job-item">
      <div class="job-header">
        <span class="job-name">{{ job.result?.name || '未命名任务' }}</span>
        <el-tag :type="statusType(job.status)" size="small">{{ statusLabel(job.status) }}</el-tag>
      </div>
      <div class="job-meta">
        <span>方法: {{ methodLabel(job.result?.method) }}</span>
        <span v-if="job.result?.raster_ids?.length">
          · {{ job.result.raster_ids.length }} 个栅格
        </span>
      </div>
      <div class="job-time">{{ formatTime(job.created_at) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fusionApi, type FusionJob } from '../api/fusionApi'
import { rasterApi } from '../api/rasterApi'
import type { RasterAsset } from '../types'

const rasters = ref<RasterAsset[]>([])
const jobs = ref<FusionJob[]>([])
const creating = ref(false)
const loadingJobs = ref(false)

const form = ref({
  name: '',
  method: 'overlay' as 'overlay' | 'weighted_sum' | 'mean',
  rasterIds: [] as string[],
})

async function fetchRasters() {
  try {
    rasters.value = (await rasterApi.list()).filter((r) => r.status === 'ready')
  } catch {
    // ignore
  }
}

async function fetchJobs() {
  loadingJobs.value = true
  try {
    jobs.value = await fusionApi.list()
  } finally {
    loadingJobs.value = false
  }
}

async function createJob() {
  if (!form.value.name.trim()) return
  creating.value = true
  try {
    const job = await fusionApi.create(form.value.name, form.value.rasterIds, form.value.method)
    jobs.value.unshift(job)
    form.value.name = ''
    form.value.rasterIds = []
    ElMessage.success('融合任务已创建')
  } catch {
    ElMessage.error('创建融合任务失败')
  } finally {
    creating.value = false
  }
}

function statusType(status: string) {
  const map: Record<string, string> = {
    PENDING: 'warning',
    STARTED: 'primary',
    SUCCESS: 'success',
    FAILURE: 'danger',
  }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    PENDING: '等待中',
    STARTED: '运行中',
    SUCCESS: '完成',
    FAILURE: '失败',
  }
  return map[status] || status
}

function methodLabel(method?: 'overlay' | 'weighted_sum' | 'mean' | string) {
  const map: Record<string, string> = {
    overlay: '叠加分析',
    weighted_sum: '加权求和',
    mean: '均值融合',
  }
  return method ? (map[method] || method) : '—'
}

function formatTime(timeStr: string) {
  try {
    return new Date(timeStr).toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

onMounted(async () => {
  await Promise.all([fetchRasters(), fetchJobs()])
})
</script>

<style scoped>
.fusion-panel {
  padding: 12px;
}

.section-title {
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 8px;
  display: block;
}

.job-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.job-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 6px;
  border: 1px solid #e0e0e0;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.job-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}

.job-meta {
  font-size: 11px;
  color: #888;
  margin-bottom: 2px;
}

.job-time {
  font-size: 10px;
  color: #aaa;
}
</style>
