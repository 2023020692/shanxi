<template>
  <div class="analytics-panel">
    <!-- Summary Cards -->
    <div class="summary-cards">
      <div class="stat-card">
        <span class="stat-value">{{ summary.well_count }}</span>
        <span class="stat-label">矿井总数</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ summary.report_count }}</span>
        <span class="stat-label">已生成报告</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ rasterReadyCount }}</span>
        <span class="stat-label">就绪栅格</span>
      </div>
    </div>

    <el-divider />

    <!-- Heatgrid Controls -->
    <div class="heatgrid-controls">
      <span class="section-title">井点密度分析</span>
      <div class="control-row">
        <span class="control-label">网格分辨率 (°)</span>
        <el-slider
          v-model="resolution"
          :min="0.1"
          :max="2.0"
          :step="0.1"
          :format-tooltip="(v: number) => v.toFixed(1) + '°'"
          style="flex: 1; margin: 0 10px"
        />
        <span class="resolution-val">{{ resolution.toFixed(1) }}°</span>
      </div>
      <el-button type="primary" size="small" :loading="loading" @click="loadHeatgrid">
        加载热力图
      </el-button>
      <el-button
        v-if="heatgridLoaded"
        type="success"
        size="small"
        @click="emit('show-heatgrid', heatgridData)"
      >
        显示到地图
      </el-button>
    </div>

    <!-- ECharts scatter chart -->
    <div v-if="heatgridLoaded" class="chart-section">
      <p class="section-title" style="margin-bottom: 6px">
        共 {{ heatgridData.total_wells }} 个井点 / {{ heatgridData.grid_cells }} 个网格
      </p>
      <div ref="chartEl" class="echarts-container"></div>
    </div>

    <el-empty v-if="!heatgridLoaded && !loading" description="点击「加载热力图」查看分析" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { analyticsApi, type HeatgridResult } from '../api/analyticsApi'

const emit = defineEmits<{
  (e: 'show-heatgrid', data: HeatgridResult): void
}>()

const loading = ref(false)
const resolution = ref(0.5)
const heatgridLoaded = ref(false)
const heatgridData = ref<HeatgridResult>({ type: 'FeatureCollection', features: [], total_wells: 0, grid_cells: 0 })
const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const summary = ref({ well_count: 0, raster_stats: {} as Record<string, number>, report_count: 0 })

const rasterReadyCount = computed(() => summary.value.raster_stats?.ready ?? 0)

async function loadSummary() {
  try {
    summary.value = await analyticsApi.getSummary()
  } catch {
    // ignore
  }
}

async function loadHeatgrid() {
  loading.value = true
  try {
    heatgridData.value = await analyticsApi.getHeatgrid(resolution.value)
    heatgridLoaded.value = true
    await nextTick()
    renderChart()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartEl.value) return
  if (!chart) {
    chart = echarts.init(chartEl.value)
  }

  const features = heatgridData.value.features
  if (!features.length) {
    chart.setOption({ title: { text: '暂无数据', left: 'center', top: 'center' } })
    return
  }

  const maxCount = Math.max(...features.map((f) => f.properties.count))
  const data = features.map((f) => [f.properties.lon, f.properties.lat, f.properties.count])

  chart.setOption({
    backgroundColor: '#1a2035',
    title: {
      text: '矿井分布热力图',
      left: 'center',
      textStyle: { color: '#ccc', fontSize: 13 },
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: { value: [number, number, number] }) =>
        `经度: ${params.value[0].toFixed(3)}<br>纬度: ${params.value[1].toFixed(3)}<br>数量: ${params.value[2]}`,
    },
    visualMap: {
      min: 1,
      max: maxCount,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: '#ccc', fontSize: 10 },
      inRange: { color: ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'] },
    },
    xAxis: {
      name: '经度',
      nameTextStyle: { color: '#aaa' },
      axisLabel: { color: '#aaa', fontSize: 10 },
      splitLine: { lineStyle: { color: '#333' } },
    },
    yAxis: {
      name: '纬度',
      nameTextStyle: { color: '#aaa' },
      axisLabel: { color: '#aaa', fontSize: 10 },
      splitLine: { lineStyle: { color: '#333' } },
    },
    series: [
      {
        type: 'scatter',
        data,
        symbolSize: (val: [number, number, number]) => Math.max(8, (val[2] / maxCount) * 36),
        encode: { x: 0, y: 1, tooltip: [0, 1, 2] },
      },
    ],
    grid: { top: 40, bottom: 50, left: 50, right: 20 },
  })
}

onMounted(loadSummary)

onUnmounted(() => {
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.analytics-panel {
  padding: 12px;
}

.summary-cards {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.stat-card {
  flex: 1;
  background: #0d47a1;
  border-radius: 6px;
  padding: 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: #fff;
}

.stat-label {
  font-size: 11px;
  color: #90caf9;
}

.heatgrid-controls {
  margin-bottom: 12px;
}

.section-title {
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 8px;
  display: block;
}

.control-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 4px;
}

.control-label {
  font-size: 12px;
  color: #888;
  white-space: nowrap;
}

.resolution-val {
  font-size: 12px;
  color: #ccc;
  width: 32px;
  text-align: right;
}

.chart-section {
  margin-top: 8px;
}

.echarts-container {
  width: 100%;
  height: 260px;
}
</style>
