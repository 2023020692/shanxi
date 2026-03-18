<template>
  <el-container class="app-container">
    <el-aside width="380px" class="sidebar">
      <div class="sidebar-header">
        <div class="system-logo">
          <el-icon class="logo-icon"><Grid /></el-icon>
          <div>
            <h2 class="system-title">煤矿资源分析系统</h2>
            <p class="system-subtitle">Coal Mine Resource Analysis System</p>
          </div>
        </div>
      </div>
      <el-tabs v-model="activeTab" type="border-card" class="sidebar-tabs">
        <el-tab-pane label="数据图层" name="datalayer">
          <DataLayerPanel :map-view-ref="mapViewRef" />
        </el-tab-pane>
        <el-tab-pane label="富集指数" name="enrichment">
          <EnrichmentPanel :map-view-ref="mapViewRef" />
        </el-tab-pane>
        <el-tab-pane label="SAM2分析" name="sam2">
          <SAM2Panel :map-view-ref="mapViewRef" @result="onSAM2Result" />
        </el-tab-pane>
        <el-tab-pane label="综合分析" name="analysis">
          <AnalysisPanel :map-view-ref="mapViewRef" :latest-s-a-m2-id="latestSAM2Id" />
        </el-tab-pane>
      </el-tabs>
    </el-aside>
    <el-main class="map-container">
      <MapView ref="mapViewRef" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Grid } from '@element-plus/icons-vue'
import MapView from '../components/MapView.vue'
import DataLayerPanel from '../components/DataLayerPanel.vue'
import EnrichmentPanel from '../components/EnrichmentPanel.vue'
import SAM2Panel from '../components/SAM2Panel.vue'
import AnalysisPanel from '../components/AnalysisPanel.vue'
import type { SAM2Result } from '../types'

const activeTab = ref('datalayer')
const mapViewRef = ref<InstanceType<typeof MapView> | null>(null)
const latestSAM2Id = ref('')

function onSAM2Result(result: SAM2Result) {
  if (result.detection_id) {
    latestSAM2Id.value = result.detection_id
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100vw;
}

.sidebar {
  display: flex;
  flex-direction: column;
  background: #0f1932;
  overflow-y: auto;
}

.sidebar-header {
  padding: 14px 16px;
  background: linear-gradient(135deg, #0d3b6e, #1565c0);
  border-bottom: 1px solid #1e3a60;
}

.system-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 28px;
  color: #64b5f6;
}

.system-title {
  font-size: 15px;
  font-weight: bold;
  color: #ffffff;
  margin: 0;
}

.system-subtitle {
  font-size: 10px;
  color: #90caf9;
  margin: 2px 0 0;
  letter-spacing: 0.5px;
}

.sidebar-tabs {
  flex: 1;
}

.map-container {
  padding: 0 !important;
  flex: 1;
  position: relative;
}
</style>
