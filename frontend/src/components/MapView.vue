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
import OSM from 'ol/source/OSM'
import XYZ from 'ol/source/XYZ'
import GeoJSON from 'ol/format/GeoJSON'
import { fromLonLat } from 'ol/proj'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import 'ol/ol.css'

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

onMounted(() => {
  map = new Map({
    target: mapEl.value!,
    layers: [
      new TileLayer({ source: new OSM() }),
      wellLayer,
    ],
    view: new View({
      center: fromLonLat([111.5, 37.5]),
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
    featureProjection: 'EPSG:3857',
  })
  wellSource.addFeatures(features)
}

defineExpose({ addRasterLayer, loadWells })
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
