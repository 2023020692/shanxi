<template>
  <div ref="mapEl" class="map-view"></div>
  <div v-if="popupInfo" class="map-popup" :style="{ left: popupPos.x + 'px', top: popupPos.y + 'px' }">
    <div class="popup-content">
      <strong>{{ popupInfo.name }}</strong>
      <div v-for="(v, k) in popupInfo.props" :key="k" class="popup-prop">
        <span class="prop-key">{{ k }}:</span> {{ v }}
      </div>
      <button class="popup-close" @click="popupInfo = null">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import WMTS from 'ol/source/WMTS'
import WMTSTileGrid from 'ol/tilegrid/WMTS'
import XYZ from 'ol/source/XYZ'
import GeoJSON from 'ol/format/GeoJSON'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from 'ol/style'
import type { HeatgridResult } from '../api/analyticsApi'
import 'ol/ol.css'

// 天地图影像服务 Token（通过环境变量 VITE_TIANDITU_TOKEN 配置）
const TIANDITU_TOKEN = import.meta.env.VITE_TIANDITU_TOKEN || '5feb116433ab9965a1460171bc2a6203'

// 天地图地理坐标系（EPSG:4326）分辨率列表（对应第 1 至 18 级）
const tiandituResolutions = [
  0.703125, 0.3515625, 0.17578125, 0.087890625,
  0.0439453125, 0.02197265625, 0.010986328125, 0.0054931640625,
  0.00274658203125, 0.001373291015625, 0.0006866455078125,
  0.00034332275390625, 0.000171661376953125, 8.58306884765625e-5,
  4.291534423828125e-5, 2.1457672119140625e-5, 1.0728836059570313e-5,
  5.364418029785156e-6,
]
const tiandituMatrixIds = Array.from({ length: 18 }, (_, i) => String(i + 1))

// 天地图影像 WMTS 数据源（img_c：地理坐标系底图）
const tiandituImgSource = new WMTS({
  url: `https://t{0-7}.tianditu.gov.cn/img_c/wmts?tk=${TIANDITU_TOKEN}`,
  layer: 'img',
  matrixSet: 'c',
  format: 'tiles',
  projection: 'EPSG:4326',
  tileGrid: new WMTSTileGrid({
    origin: [-180, 90],
    resolutions: tiandituResolutions,
    matrixIds: tiandituMatrixIds,
  }),
  style: 'default',
  wrapX: true,
  crossOrigin: 'anonymous',
})

const mapEl = ref<HTMLDivElement | null>(null)
let map: Map | null = null
const popupInfo = ref<{ name: string; props: Record<string, unknown> } | null>(null)
const popupPos = ref({ x: 0, y: 0 })

const wellSource = new VectorSource()
const wellLayer = new VectorLayer({
  source: wellSource,
  style: new Style({
    image: new CircleStyle({
      radius: 6,
      fill: new Fill({ color: '#ff6b35' }),
      stroke: new Stroke({ color: '#fff', width: 2 }),
    }),
  }),
})

const heatgridSource = new VectorSource()
const heatgridLayer = new VectorLayer({
  source: heatgridSource,
  visible: false,
})

onMounted(() => {
  map = new Map({
    target: mapEl.value!,
    layers: [
      new TileLayer({ source: tiandituImgSource }),
      heatgridLayer,
      wellLayer,
    ],
    view: new View({
      projection: 'EPSG:4326',
      center: [111.5, 37.5],
      zoom: 7,
    }),
  })

  map.on('click', (evt) => {
    const features = map!.getFeaturesAtPixel(evt.pixel)
    if (features && features.length > 0) {
      const feat = features[0]
      const props = feat.getProperties()
      const { geometry: _g, ...rest } = props
      popupInfo.value = { name: props.name || 'Well', props: rest }
      popupPos.value = { x: evt.pixel[0] + 10, y: evt.pixel[1] + 10 }
    } else {
      popupInfo.value = null
    }
  })
})

onUnmounted(() => {
  map?.setTarget(undefined)
})

function addRasterLayer(url: string, name: string) {
  const layer = new TileLayer({
    source: new XYZ({ url }),
    opacity: 0.8,
  })
  ;(layer as unknown as { _name: string })._name = name
  map?.addLayer(layer)
}

async function loadWells() {
  const res = await fetch('/api/wells')
  const geojson = await res.json()
  wellSource.clear()
  const features = new GeoJSON().readFeatures(geojson, {
    featureProjection: 'EPSG:4326',
  })
  wellSource.addFeatures(features)
}

function showHeatgrid(data: HeatgridResult) {
  heatgridSource.clear()
  if (!data.features.length) return

  const maxCount = Math.max(...data.features.map((f) => f.properties.count))

  const features = data.features.map((f) => {
    const { count, lon, lat } = f.properties
    const ratio = count / maxCount
    const r = Math.round(255 * Math.min(1, ratio * 2))
    const g = Math.round(255 * Math.max(0, 1 - ratio * 2))
    const radius = Math.max(8, Math.round(ratio * 28))

    const feat = new Feature({
      geometry: new Point([lon, lat]),
      count,
    })
    feat.setStyle(
      new Style({
        image: new CircleStyle({
          radius,
          fill: new Fill({ color: `rgba(${r}, ${g}, 50, 0.65)` }),
          stroke: new Stroke({ color: 'rgba(255,255,255,0.4)', width: 1 }),
        }),
        text: count > 1
          ? new Text({
              text: String(count),
              fill: new Fill({ color: '#fff' }),
              font: 'bold 10px sans-serif',
            })
          : undefined,
      }),
    )
    return feat
  })

  heatgridSource.addFeatures(features)
  heatgridLayer.setVisible(true)
}

defineExpose({ addRasterLayer, loadWells, showHeatgrid })
</script>

<style scoped>
.map-view {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map-popup {
  position: absolute;
  z-index: 1000;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  min-width: 160px;
  max-width: 280px;
}

.popup-content {
  padding: 12px;
  position: relative;
}

.popup-prop {
  font-size: 12px;
  margin-top: 4px;
}

.prop-key {
  font-weight: bold;
  color: #555;
}

.popup-close {
  position: absolute;
  top: 4px;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: #999;
}
</style>
