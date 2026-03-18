<template>
  <div class="upload-panel">
    <p class="section-title">上传栅格数据 (.tif)</p>

    <input ref="fileInput" type="file" accept=".tif" style="display:none" @change="handleUpload" />
    <el-button type="primary" @click="fileInput?.click()" :loading="uploading" :disabled="uploading">
      选择并上传 TIF 文件
    </el-button>

    <el-progress v-if="uploading" :percentage="uploadProgress" style="margin-top: 12px" />

    <div v-if="uploadedRaster" class="uploaded-info">
      <el-alert type="success" :closable="false">
        <template #title>
          上传成功: {{ uploadedRaster.filename }}
        </template>
      </el-alert>

      <el-button
        type="warning"
        style="margin-top: 8px"
        @click="startPreprocess"
        :loading="preprocessing"
        :disabled="preprocessing || !!taskId"
      >
        启动预处理 (COG转换)
      </el-button>
    </div>

    <div v-if="taskId" style="margin-top: 12px">
      <p class="section-title">处理状态</p>
      <TaskStatus :task-id="taskId" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { RasterAsset } from '../types'
import { rasterApi } from '../api/rasterApi'
import TaskStatus from './TaskStatus.vue'

const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadedRaster = ref<RasterAsset | null>(null)
const preprocessing = ref(false)
const taskId = ref<string | null>(null)

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]

  uploading.value = true
  uploadProgress.value = 0
  taskId.value = null
  uploadedRaster.value = null

  try {
    uploadProgress.value = 30
    const raster = await rasterApi.upload(file)
    uploadProgress.value = 100
    uploadedRaster.value = raster
  } catch (e) {
    console.error(e)
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function startPreprocess() {
  if (!uploadedRaster.value) return
  preprocessing.value = true
  try {
    const res = await rasterApi.preprocess(uploadedRaster.value.id)
    taskId.value = res.task_id
  } finally {
    preprocessing.value = false
  }
}
</script>

<style scoped>
.upload-panel {
  padding: 12px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.uploaded-info {
  margin-top: 12px;
}
</style>
