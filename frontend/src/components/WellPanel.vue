<template>
  <div class="well-panel">
    <div class="import-section">
      <p class="section-title">导入井点数据</p>
      <p class="hint">Excel文件需包含: name(井名), lon(经度), lat(纬度) 列</p>
      <input ref="fileInput" type="file" accept=".xlsx" style="display:none" @change="handleFileChange" />
      <el-button type="primary" @click="fileInput?.click()" :loading="importing">
        导入井点 Excel
      </el-button>
      <el-alert v-if="importResult" :title="importResult" type="success" :closable="false" style="margin-top: 8px" />
      <el-alert v-if="importError" :title="importError" type="error" :closable="false" style="margin-top: 8px" />
    </div>

    <el-divider />

    <div class="display-section">
      <el-button type="success" @click="showWells" :loading="loadingWells">
        显示井点
      </el-button>
      <p v-if="wellCount !== null" class="well-count">已加载 {{ wellCount }} 个井点</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { wellApi } from '../api/wellApi'

const props = defineProps<{ mapViewRef: { loadWells: () => Promise<void> } | null }>()

const fileInput = ref<HTMLInputElement | null>(null)
const importing = ref(false)
const importResult = ref('')
const importError = ref('')
const loadingWells = ref(false)
const wellCount = ref<number | null>(null)

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  importing.value = true
  importResult.value = ''
  importError.value = ''
  try {
    const res = await wellApi.importExcel(file)
    importResult.value = `成功导入 ${res.imported} 个井点`
  } catch (e: unknown) {
    importError.value = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '导入失败'
  } finally {
    importing.value = false
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
</script>

<style scoped>
.well-panel {
  padding: 12px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 6px;
}

.hint {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}

.display-section {
  text-align: center;
}

.well-count {
  margin-top: 8px;
  color: #67c23a;
  font-size: 13px;
}
</style>
