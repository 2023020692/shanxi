<template>
  <div class="map-container" ref="mapContainer">
    <div ref="mapEl" class="map-view"></div>
    <canvas ref="deckCanvas" class="deck-canvas"></canvas>
  </div>
  <div v-if="popupInfo" class="map-popup" :style="{ left: popupPos.x + 'px', top: popupPos.y + 'px' }">
    <div class="popup-content">
      <strong>{{ popupInfo.name }}</strong>
      <div v-for="(v, k) in popupInfo.props" :key="k" class="popup-prop">
        <span class="prop-key">{{ k }}:</span> {{ v }}
      </div>
      <button class="popup-close" @click="popupInfo = null">×</button>
    </div>
  </div>
  <!-- Color bar legend -->
  <div v-if="colorBarVisible" class="color-bar-panel">
    <p class="color-bar-title">{{ colorBarTitle }}</p>
    <div class="color-bar-gradient" :style="{ background: colorBarGradient }"></div>
    <div class="color-bar-labels">
      <span>{{ colorBarMin }}</span>
      <span>{{ colorBarMax }}</span>
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
import type { EnrichmentGridPoint } from '../types'
import 'ol/ol.css'
import { Deck } from '@deck.gl/core'
import { BitmapLayer } from '@deck.gl/layers'
import { fromUrl } from 'geotiff'

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

const mapContainer = ref<HTMLDivElement | null>(null)
const mapEl = ref<HTMLDivElement | null>(null)
const deckCanvas = ref<HTMLCanvasElement | null>(null)
let map: Map | null = null
let deck: Deck | null = null
const popupInfo = ref<{ name: string; props: Record<string, unknown> } | null>(null)
const popupPos = ref({ x: 0, y: 0 })

// Color bar state
const colorBarVisible = ref(false)
const colorBarTitle = ref('')
const colorBarGradient = ref('')
const colorBarMin = ref('')
const colorBarMax = ref('')

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

const enrichmentSource = new VectorSource()
const enrichmentLayer = new VectorLayer({
  source: enrichmentSource,
  visible: false,
})

const sam2Source = new VectorSource()
const sam2Layer = new VectorLayer({
  source: sam2Source,
  visible: false,
})

/** Sync Deck.gl viewport to match the current OpenLayers view. */
function syncDeckViewState() {
  if (!map || !deck) return
  const view = map.getView()
  const center = view.getCenter()
  const zoom = view.getZoom()
  if (center && zoom !== undefined) {
    deck.setProps({
      viewState: {
        longitude: center[0],
        latitude: center[1],
        zoom: zoom,
        pitch: 0,
        bearing: 0,
      },
    })
  }
}

onMounted(() => {
  map = new Map({
    target: mapEl.value!,
    layers: [
      new TileLayer({ source: tiandituImgSource }),
      heatgridLayer,
      enrichmentLayer,
      sam2Layer,
      wellLayer,
    ],
    view: new View({
      projection: 'EPSG:4326',
      center: [111.5, 37.5],
      zoom: 7,
    }),
  })

  // Initialise Deck.gl WebGL overlay (controller:false – OL owns navigation)
  if (deckCanvas.value) {
    deck = new Deck({
      canvas: deckCanvas.value,
      width: '100%',
      height: '100%',
      initialViewState: {
        longitude: 111.5,
        latitude: 37.5,
        zoom: 7,
        pitch: 0,
        bearing: 0,
      },
      controller: false,
      layers: [],
    })
  }

  // Keep Deck.gl viewport in sync with OL map movements
  map.on('moveend', syncDeckViewState)
  map.on('postrender', syncDeckViewState)

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
  deck?.finalize()
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

/**
 * Render a GeoTIFF file using geotiff.js (for proper geo-referencing) and
 * Deck.gl BitmapLayer (WebGL/GPU-accelerated).
 *
 * If the file is accessible via tifUrl the TIF is fetched, its bounding box
 * is extracted from the embedded GeoTransform/CRS information, and the band
 * data is colourised with the chosen colormap before being handed to Deck.gl.
 * Falls back to the grid-point approach when no tifUrl is provided.
 */
async function renderTifLayer(
  tifUrl: string,
  colormap: string,
  title: string,
): Promise<void> {
  if (!deck) return

  try {
    // Use geotiff.js to read GeoTransform and CRS, ensuring correct geographic placement
    const tiff = await fromUrl(tifUrl)
    const image = await tiff.getImage()

    // getBoundingBox() returns [west, south, east, north] using the embedded GeoTransform
    const [west, south, east, north] = image.getBoundingBox()

    const width = image.getWidth()
    const height = image.getHeight()

    // Read all rasters (first band used for single-band data)
    const rasters = await image.readRasters()
    const band = rasters[0] as Float32Array | Uint8Array | Int16Array

    // Normalise band values to [0, 1]
    let minVal = Infinity
    let maxVal = -Infinity
    for (let i = 0; i < band.length; i++) {
      if (band[i] < minVal) minVal = band[i]
      if (band[i] > maxVal) maxVal = band[i]
    }
    const range = maxVal - minVal || 1

    // Build a colourised RGBA image using the selected colormap (CPU → GPU via BitmapLayer)
    const imageCanvas = document.createElement('canvas')
    imageCanvas.width = width
    imageCanvas.height = height
    const ctx = imageCanvas.getContext('2d')!
    const imgData = ctx.createImageData(width, height)

    for (let i = 0; i < band.length; i++) {
      const t = (band[i] - minVal) / range
      const [r, g, b, a] = colormapRGBA(colormap, t)
      imgData.data[i * 4] = r
      imgData.data[i * 4 + 1] = g
      imgData.data[i * 4 + 2] = b
      imgData.data[i * 4 + 3] = a
    }
    ctx.putImageData(imgData, 0, 0)

    // Hand the geo-referenced bitmap to Deck.gl for WebGL/GPU rendering
    deck.setProps({
      layers: [
        new BitmapLayer({
          id: 'geotiff-layer',
          bounds: [west, south, east, north] as [number, number, number, number],
          image: imageCanvas.toDataURL(),
          opacity: 0.75,
        }),
      ],
    })

    // Update the color bar legend
    colorBarTitle.value = title
    colorBarGradient.value = buildGradient(colormap)
    colorBarMin.value = minVal.toFixed(2)
    colorBarMax.value = maxVal.toFixed(2)
    colorBarVisible.value = true

    // Hide the old OL vector layers since Deck.gl takes over
    enrichmentLayer.setVisible(false)
    sam2Layer.setVisible(false)
  } catch (err) {
    console.warn('renderTifLayer: geotiff read failed, falling back to grid render', err)
    throw err
  }
}

/** Clear the Deck.gl TIF layer. */
function clearTifLayer() {
  deck?.setProps({ layers: [] })
  colorBarVisible.value = false
}

/** Render enrichment index grid onto the map with the given colormap. */
function showEnrichmentLayer(grid: EnrichmentGridPoint[], colormap: string, name: string) {
  enrichmentSource.clear()

  if (!grid.length) return

  const maxVal = Math.max(...grid.map((p) => p.value))
  const minVal = Math.min(...grid.map((p) => p.value))
  const range = maxVal - minVal || 1

  const features = grid.map((p) => {
    const t = (p.value - minVal) / range  // 0..1
    const color = colormapColor(colormap, t)
    const feat = new Feature({ geometry: new Point([p.lon, p.lat]), value: p.value })
    feat.setStyle(
      new Style({
        image: new CircleStyle({
          radius: 10,
          fill: new Fill({ color }),
          stroke: new Stroke({ color: 'rgba(255,255,255,0.2)', width: 1 }),
        }),
      }),
    )
    return feat
  })

  enrichmentSource.addFeatures(features)
  enrichmentLayer.setVisible(true)

  // Show color bar
  colorBarTitle.value = name + ' - 富集指数'
  colorBarGradient.value = buildGradient(colormap)
  colorBarMin.value = minVal.toFixed(2)
  colorBarMax.value = maxVal.toFixed(2)
  colorBarVisible.value = true
}

/** Render SAM2 heatmap grid onto the map. */
function showSAM2Heatmap(
  grid: Array<{ lon: number; lat: number; intensity: number }>,
  colormap: string,
) {
  sam2Source.clear()
  if (!grid.length) return

  const maxI = Math.max(...grid.map((p) => p.intensity))
  const minI = Math.min(...grid.map((p) => p.intensity))
  const range = maxI - minI || 1

  const features = grid.map((p) => {
    const t = (p.intensity - minI) / range
    const color = colormapColor(colormap, t)
    const feat = new Feature({ geometry: new Point([p.lon, p.lat]), intensity: p.intensity })
    feat.setStyle(
      new Style({
        image: new CircleStyle({
          radius: 12,
          fill: new Fill({ color }),
          stroke: new Stroke({ color: 'rgba(255,255,255,0.15)', width: 1 }),
        }),
      }),
    )
    return feat
  })

  sam2Source.addFeatures(features)
  sam2Layer.setVisible(true)

  colorBarTitle.value = 'SAM2 热力图'
  colorBarGradient.value = buildGradient(colormap)
  colorBarMin.value = minI.toFixed(2)
  colorBarMax.value = maxI.toFixed(2)
  colorBarVisible.value = true
}

/** Map a normalised t ∈ [0,1] to an RGBA color string for a named colormap. */
function colormapColor(name: string, t: number): string {
  const [r, g, b, a] = colormapRGBA(name, t)
  return `rgba(${r},${g},${b},${(a / 255).toFixed(2)})`
}

/** Map a normalised t ∈ [0,1] to [R,G,B,A] (0-255) for a named colormap. */
function colormapRGBA(name: string, t: number): [number, number, number, number] {
  switch (name) {
    case 'hot': {
      const r = Math.round(Math.min(1, t * 3) * 255)
      const g = Math.round(Math.max(0, t * 3 - 1) * 255)
      const b = Math.round(Math.max(0, t * 3 - 2) * 255)
      return [r, g, b, 191]
    }
    case 'plasma': {
      const r = Math.round((0.05 + t * 0.9) * 255)
      const g = Math.round(Math.max(0, (0.5 - Math.abs(t - 0.5)) * 2) * 180)
      const b = Math.round((1 - t) * 200)
      return [r, g, b, 191]
    }
    case 'inferno': {
      const r = Math.round(t * 255)
      const g = Math.round(t * t * 180)
      const b = Math.round(Math.max(0, (0.5 - t) * 2) * 200)
      return [r, g, b, 191]
    }
    case 'viridis': {
      const r = Math.round((0.26 + t * 0.66) * 255)
      const g = Math.round((0.0 + t * 0.89) * 255)
      const b = Math.round((0.33 + (0.5 - Math.abs(t - 0.5)) * 0.6) * 255)
      return [r, g, b, 191]
    }
    case 'RdYlGn': {
      const r = t < 0.5 ? 255 : Math.round((1 - (t - 0.5) * 2) * 255)
      const g = t < 0.5 ? Math.round(t * 2 * 255) : 255
      return [r, g, 0, 191]
    }
    default: {
      // rainbow
      const r = Math.round(Math.abs(t * 2 - 0.5) * 255)
      const g = Math.round(Math.sin(t * Math.PI) * 255)
      const b = Math.round((1 - t) * 255)
      return [r, g, b, 191]
    }
  }
}

/** Build a CSS linear-gradient string for the color bar. */
function buildGradient(name: string): string {
  const stops = [0, 0.25, 0.5, 0.75, 1]
    .map((t) => {
      const c = colormapColor(name, t)
        .replace(/[\d.]+\)$/, '1)')  // fully opaque in legend
      return `${c} ${t * 100}%`
    })
    .join(', ')
  return `linear-gradient(to right, ${stops})`
}

defineExpose({ addRasterLayer, loadWells, showHeatgrid, showEnrichmentLayer, showSAM2Heatmap, renderTifLayer, clearTifLayer })
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map-view {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.deck-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
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

.color-bar-panel {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 500;
  background: rgba(15, 25, 50, 0.85);
  border-radius: 6px;
  padding: 6px 12px;
  min-width: 200px;
  backdrop-filter: blur(4px);
}

.color-bar-title {
  font-size: 11px;
  color: #ccc;
  text-align: center;
  margin-bottom: 4px;
}

.color-bar-gradient {
  height: 12px;
  border-radius: 3px;
  margin-bottom: 2px;
}

.color-bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #aaa;
}
</style>
