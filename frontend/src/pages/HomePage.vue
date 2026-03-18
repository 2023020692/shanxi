<template>
  <el-container class="app-container">
    <el-aside width="360px" class="sidebar">
      <div class="sidebar-header">
        <h2>山西省 WebGIS 平台</h2>
      </div>
      <el-tabs v-model="activeTab" type="border-card" class="sidebar-tabs">
        <el-tab-pane label="图层" name="layers">
          <LayerPanel :map-view-ref="mapViewRef" />
        </el-tab-pane>
        <el-tab-pane label="井点" name="wells">
          <WellPanel :map-view-ref="mapViewRef" />
        </el-tab-pane>
        <el-tab-pane label="上传" name="upload">
          <UploadPanel />
        </el-tab-pane>
        <el-tab-pane label="报告" name="reports">
          <ReportPanel />
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
import MapView from '../components/MapView.vue'
import LayerPanel from '../components/LayerPanel.vue'
import WellPanel from '../components/WellPanel.vue'
import UploadPanel from '../components/UploadPanel.vue'
import ReportPanel from '../components/ReportPanel.vue'

const activeTab = ref('layers')
const mapViewRef = ref<InstanceType<typeof MapView> | null>(null)
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100vw;
}

.sidebar {
  display: flex;
  flex-direction: column;
  background: #1a2035;
  overflow-y: auto;
}

.sidebar-header {
  padding: 16px;
  background: #0d47a1;
  color: white;
}

.sidebar-header h2 {
  font-size: 16px;
  font-weight: bold;
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
