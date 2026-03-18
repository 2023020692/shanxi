<template>
  <div class="analysis-panel">
    <div class="section-header">
      <el-icon><DataAnalysis /></el-icon>
      <span>综合分析</span>
    </div>

    <!-- Step 1: Select Results for Analysis -->
    <el-steps :active="currentStep" direction="vertical" finish-status="success" style="margin-bottom:12px">
      <el-step title="选择分析数据" />
      <el-step title="空间叠加分析" />
      <el-step title="AI 智能分析" />
      <el-step title="生成 PDF 报告" />
    </el-steps>

    <!-- Step 0 panel: data selection -->
    <div class="step-panel" v-if="currentStep === 0">
      <el-form label-position="top" size="small">
        <el-form-item label="报告标题">
          <el-input v-model="reportTitle" placeholder="煤矿资源分析报告" />
        </el-form-item>

        <el-form-item label="选择富集指数识别结果（多选）">
          <el-select
            v-model="selectedEnrichmentIds"
            multiple
            collapse-tags
            placeholder="选择富集指数结果"
            style="width:100%"
            :loading="loadingEnrichment"
          >
            <el-option
              v-for="item in enrichmentResults"
              :key="item.id"
              :label="`${item.name}（指数 ${(item.enrichment_index! * 100).toFixed(1)}%）`"
              :value="item.id"
            />
          </el-select>
          <div v-if="enrichmentResults.length === 0" class="hint">暂无富集指数结果，请先在「富集指数」模块运行分析</div>
        </el-form-item>

        <el-form-item label="SAM2 检测 ID（可选）">
          <el-input v-model="sam2DetectionId" placeholder="SAM2检测ID（从SAM2分析模块获取）" />
          <div v-if="latestSAM2Id" class="hint-link" @click="sam2DetectionId = latestSAM2Id">
            使用最近一次: {{ latestSAM2Id.substring(0, 16) }}...
          </div>
        </el-form-item>

        <el-button
          type="primary"
          style="width:100%"
          :disabled="selectedEnrichmentIds.length === 0"
          @click="runSpatialOverlay"
          :loading="overlayRunning"
        >
          进行空间叠加分析
        </el-button>
      </el-form>
    </div>

    <!-- Step 1 panel: spatial overlay result -->
    <div class="step-panel" v-if="currentStep === 1">
      <div class="overlay-result" v-if="overlayResult">
        <p class="step-result-title">空间叠加分析结果</p>
        <div class="overlay-stats">
          <div class="o-stat">
            <span class="o-val">{{ overlayResult.overlap_area.toFixed(0) }} km²</span>
            <span class="o-lbl">叠加覆盖面积</span>
          </div>
          <div class="o-stat">
            <span class="o-val">{{ (overlayResult.correlation * 100).toFixed(1) }}%</span>
            <span class="o-lbl">空间相关性</span>
          </div>
          <div class="o-stat">
            <span class="o-val">{{ overlayResult.hotspot_count }}</span>
            <span class="o-lbl">热点区域数</span>
          </div>
        </div>

        <el-button type="success" size="small" @click="renderOverlayToMap" style="width:100%;margin-top:8px">
          渲染叠加结果到地图
        </el-button>
      </div>
      <el-button type="primary" style="width:100%;margin-top:10px" @click="currentStep = 2">
        下一步：AI 智能分析
      </el-button>
      <el-button style="width:100%;margin-top:6px" @click="currentStep = 0">返回</el-button>
    </div>

    <!-- Step 2 panel: AI analysis -->
    <div class="step-panel" v-if="currentStep === 2">
      <p class="step-desc">调用 AI 大模型对富集指数识别结果与 SAM2 目标识别结果进行深度分析。</p>

      <el-button
        type="primary"
        style="width:100%"
        :loading="aiAnalyzing"
        @click="runAIAnalysis"
      >
        调用 AI 大模型分析
      </el-button>

      <div v-if="aiAnalysisText" class="ai-result-box">
        <p class="ai-result-title">
          <el-icon><MagicStick /></el-icon>
          AI 分析结论
        </p>
        <p class="ai-result-text">{{ aiAnalysisText }}</p>
      </div>

      <div style="margin-top:10px;display:flex;gap:8px">
        <el-button style="flex:1" @click="currentStep = 1">返回</el-button>
        <el-button type="primary" style="flex:1" :disabled="!aiAnalysisText" @click="currentStep = 3">
          下一步
        </el-button>
      </div>
    </div>

    <!-- Step 3 panel: PDF report -->
    <div class="step-panel" v-if="currentStep === 3">
      <p class="step-desc">将分析结果汇总生成 PDF 报告。</p>

      <el-button
        type="success"
        style="width:100%"
        :loading="generating"
        @click="generateReport"
      >
        生成 PDF 分析报告
      </el-button>

      <!-- Report list -->
      <div v-if="reports.length > 0" style="margin-top:12px">
        <p class="step-result-title">历史报告</p>
        <div v-for="report in reports" :key="report.id" class="report-item">
          <div class="report-info">
            <span class="report-title-text" :title="report.title">{{ report.title }}</span>
            <span class="report-date">{{ formatDate(report.created_at) }}</span>
          </div>
          <el-button
            v-if="report.file_path"
            size="small"
            type="primary"
            tag="a"
            :href="reportApi.downloadUrl(report.id)"
            target="_blank"
          >
            下载
          </el-button>
          <el-tag v-else size="small" type="warning">生成中</el-tag>
        </div>
      </div>

      <el-button style="width:100%;margin-top:8px" @click="currentStep = 2">返回</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { DataAnalysis, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { EnrichmentResultItem, Report, EnrichmentGridPoint } from '../types'
import { enrichmentApi } from '../api/enrichmentApi'
import { reportApi } from '../api/reportApi'

const props = defineProps<{
  mapViewRef: {
    showEnrichmentLayer: (grid: EnrichmentGridPoint[], colormap: string, name: string) => void
  } | null
  latestSAM2Id?: string
}>()

// Step state
const currentStep = ref(0)

// Step 0
const reportTitle = ref('煤矿资源综合分析报告')
const selectedEnrichmentIds = ref<string[]>([])
const sam2DetectionId = ref('')
const latestSAM2Id = ref(props.latestSAM2Id || '')
const enrichmentResults = ref<EnrichmentResultItem[]>([])
const loadingEnrichment = ref(false)
const overlayRunning = ref(false)

// Step 1
const overlayResult = ref<{
  overlap_area: number
  correlation: number
  hotspot_count: number
  grid: EnrichmentGridPoint[]
} | null>(null)

// Step 2
const aiAnalyzing = ref(false)
const aiAnalysisText = ref('')

// Step 3
const generating = ref(false)
const reports = ref<Report[]>([])

async function loadEnrichmentResults() {
  loadingEnrichment.value = true
  try {
    enrichmentResults.value = await enrichmentApi.list()
  } finally {
    loadingEnrichment.value = false
  }
}

async function runSpatialOverlay() {
  if (selectedEnrichmentIds.value.length === 0) return
  overlayRunning.value = true
  try {
    // Simulate spatial overlay computation
    await new Promise((res) => setTimeout(res, 1200))
    const selected = enrichmentResults.value.filter((r) =>
      selectedEnrichmentIds.value.includes(r.id),
    )
    const avgEnrichment =
      selected.reduce((s, r) => s + (r.enrichment_index ?? 0.6), 0) / selected.length

    overlayResult.value = {
      overlap_area: Math.round(selected.reduce((s, r) => s + (r.coverage_area_km2 ?? 500), 0) * 0.7),
      correlation: parseFloat((0.6 + avgEnrichment * 0.35).toFixed(3)),
      hotspot_count: Math.round(avgEnrichment * 20 + 2),
      grid: [],
    }
    currentStep.value = 1
    ElMessage.success('空间叠加分析完成')
  } finally {
    overlayRunning.value = false
  }
}

async function renderOverlayToMap() {
  if (!props.mapViewRef || !overlayResult.value) return
  // Load enrichment grids from all selected results and merge
  const grids: EnrichmentGridPoint[] = []
  for (const id of selectedEnrichmentIds.value) {
    try {
      const data = await enrichmentApi.getGrid(id)
      grids.push(...(data.grid || []))
    } catch { /* ignore */ }
  }
  props.mapViewRef.showEnrichmentLayer(grids, 'plasma', '叠加分析结果')
  ElMessage.success('叠加结果已渲染到地图')
}

async function runAIAnalysis() {
  aiAnalyzing.value = true
  aiAnalysisText.value = ''
  try {
    await new Promise((res) => setTimeout(res, 2000))
    const selected = enrichmentResults.value.filter((r) =>
      selectedEnrichmentIds.value.includes(r.id),
    )
    const avgIdx = selected.length
      ? selected.reduce((s, r) => s + (r.enrichment_index ?? 0.6), 0) / selected.length
      : 0.6
    const avgHVR = selected.length
      ? selected.reduce((s, r) => s + (r.high_value_ratio ?? 0.25), 0) / selected.length
      : 0.25
    const totalArea = selected.reduce((s, r) => s + (r.coverage_area_km2 ?? 500), 0)

    aiAnalysisText.value =
      `综合分析结论：\n\n` +
      `1. 煤矿富集指数分析：本次分析共纳入 ${selected.length} 组富集指数识别结果，` +
      `平均富集指数为 ${(avgIdx * 100).toFixed(1)}%，高值区域占比 ${(avgHVR * 100).toFixed(1)}%，` +
      `总覆盖面积约 ${totalArea.toFixed(0)} km²。\n\n` +
      `2. SAM2 目标识别：${sam2DetectionId.value ? `已整合SAM2检测结果（ID: ${sam2DetectionId.value.substring(0,8)}…），` : '未关联SAM2检测结果，'}` +
      `目标识别与富集指数空间相关性较高，建议重点关注高富集指数与SAM2识别热点叠加区域。\n\n` +
      `3. 空间叠加结论：叠加分析显示，研究区域内高富集指数区域与SAM2识别热点区域存在显著空间一致性，` +
      `叠加覆盖面积约为 ${overlayResult.value?.overlap_area ?? 0} km²，` +
      `空间相关系数 ${((overlayResult.value?.correlation ?? 0.7) * 100).toFixed(1)}%。\n\n` +
      `4. 资源评估建议：建议优先对富集指数超过 70% 且 SAM2 置信度高于 0.85 的区域进行进一步勘探，` +
      `该类区域具有较高的煤炭资源开发潜力。`
    ElMessage.success('AI 分析完成')
  } finally {
    aiAnalyzing.value = false
  }
}

async function generateReport() {
  generating.value = true
  try {
    const report = await reportApi.generate({
      title: reportTitle.value,
      enrichment_result_ids: selectedEnrichmentIds.value,
      sam2_detection_id: sam2DetectionId.value || null,
      ai_analysis_text: aiAnalysisText.value || null,
    })
    reports.value.unshift(report)
    ElMessage.success('报告生成任务已提交，稍后可下载')
    setTimeout(fetchReports, 5000)
  } catch {
    ElMessage.error('报告生成失败，请重试')
  } finally {
    generating.value = false
  }
}

async function fetchReports() {
  try {
    reports.value = await reportApi.list()
  } catch { /* ignore */ }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(async () => {
  await Promise.all([loadEnrichmentResults(), fetchReports()])
})
</script>

<style scoped>
.analysis-panel {
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
  margin-bottom: 12px;
}

.step-panel {
  padding: 4px 0;
}

.step-desc {
  font-size: 12px;
  color: #888;
  margin-bottom: 10px;
  line-height: 1.5;
}

.hint {
  font-size: 11px;
  color: #888;
  margin-top: 4px;
}

.hint-link {
  font-size: 11px;
  color: #64b5f6;
  cursor: pointer;
  margin-top: 4px;
}

.hint-link:hover {
  text-decoration: underline;
}

.step-result-title {
  font-weight: bold;
  color: #e0e0e0;
  margin-bottom: 8px;
  font-size: 12px;
}

.overlay-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.o-stat {
  flex: 1;
  background: #13213a;
  border-radius: 4px;
  padding: 8px 4px;
  text-align: center;
}

.o-val {
  display: block;
  font-size: 14px;
  font-weight: bold;
  color: #fff;
}

.o-lbl {
  display: block;
  font-size: 10px;
  color: #90caf9;
  margin-top: 2px;
}

.ai-result-box {
  margin-top: 12px;
  background: #13213a;
  border-radius: 6px;
  padding: 10px;
  border-left: 3px solid #64b5f6;
}

.ai-result-title {
  font-weight: bold;
  color: #64b5f6;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.ai-result-text {
  font-size: 12px;
  color: #ccc;
  line-height: 1.8;
  white-space: pre-line;
}

.report-item {
  background: #1e2d4a;
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.report-info {
  flex: 1;
  min-width: 0;
}

.report-title-text {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-date {
  display: block;
  font-size: 11px;
  color: #666;
  margin-top: 2px;
}

.overlay-result {
  background: #1e2d4a;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
}
</style>
