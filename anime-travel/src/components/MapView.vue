<template>
  <div class="map-container">
    <div ref="mapRef" class="map-element"></div>
    <div v-if="loading" class="map-loading">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'
import { storeToRefs } from 'pinia'
import { planDrivingRoute, planWalkingRoute, planCyclingRoute } from '../utils/orsRoute'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const store = useAppStore()
const { points, selectedPointId, libraryItinerary, defaultCenter, defaultZoom, bangumi, loading, coordinateLibrary, routeType } = storeToRefs(store)

const mapRef = ref(null)
let map = null
let markers = []
let routePolylines = []

const dayColors = [
  '#409EFF',
  '#67C23A',
  '#E6A23C',
  '#F56C6C',
  '#909399',
  '#b37feb',
  '#36cfc9'
]

function createMarkerContent(index, day, checked) {
  const color = day ? dayColors[(day - 1) % dayColors.length] : '#409EFF'
  const opacity = checked ? 1 : 0.6
  const size = checked ? 28 : 22
  
  return `<div class="custom-marker" style="
    background-color:${color};
    opacity:${opacity};
    width:${size}px;
    height:${size}px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    color:white;
    font-weight:bold;
    font-size:${checked ? 13 : 10}px;
    border:2px solid white;
    box-shadow:0 2px 8px rgba(0,0,0,0.4);
    cursor:pointer;
    position:relative;
  ">${index + 1}</div>`
}

function createPopupContent(point) {
  const inLibrary = store.isInLibrary(point.id)
  let html = `<div class="landmark-popup">`
  html += `<div class="popup-title">${point.name}</div>`
  if (point.image) {
    const imgUrl = point.image.includes('?') ? point.image : point.image + '?plan=h160'
    html += `<img src="${imgUrl}" alt="${point.name}" class="popup-image" />`
  }
  html += `<div class="popup-info">`
  if (point.ep) html += `<span>EP${point.ep}</span>`
  if (point.s) html += `<span>${formatTime(point.s)}</span>`
  if (point.day) html += `<span class="popup-day">第${point.day}天</span>`
  html += `</div>`
  if (point.origin) {
    html += `<div class="popup-origin">来源: `
    if (point.originURL) {
      html += `<a href="${point.originURL}" target="_blank">${point.origin}</a>`
    } else {
      html += point.origin
    }
    html += `</div>`
  }
  const btnClass = inLibrary ? 'is-added' : ''
  const btnText = inLibrary ? '★ 已收藏' : '☆ 收藏'
  html += `<div class="popup-footer">`
  html += `<button class="popup-library-btn ${btnClass}" data-point-id="${point.id}">${btnText}</button>`
  html += `</div></div>`
  return html
}

function formatTime(seconds) {
  if (!seconds) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${m}:${String(s).padStart(2, '0')}`
}

function initMap() {
  if (!mapRef.value) return

  let center = defaultCenter.value
  let zoom = defaultZoom.value || 10

  if (!center || center.length !== 2 || (center[0] === 0 && center[1] === 0)) {
    center = [35.6895, 139.6917]
  }

  map = L.map(mapRef.value, {
    center: center,
    zoom: zoom,
    zoomControl: true,
    attributionControl: false
  })

  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map)

  if (mapRef.value) {
    mapRef.value.addEventListener('click', function(e) {
      const target = e.target
      if (target.classList && target.classList.contains('popup-library-btn')) {
        const pointId = target.getAttribute('data-point-id')
        if (pointId) {
          if (store.isInLibrary(pointId)) {
            store.removeFromLibrary(pointId)
          } else {
            const point = points.value.find(function(p) { return p.id === pointId })
            if (point) store.addToLibrary(point)
          }
        }
      }
    })
  }

  setTimeout(() => {
    updateMarkers()
  }, 500)
}

function updateMarkers() {
  if (!map) return

  markers.forEach(m => map.removeLayer(m))
  markers = []

  routePolylines.forEach(p => map.removeLayer(p))
  routePolylines = []

  points.value.forEach(function(point, index) {
    if (!point.geo || point.geo.length !== 2) return

    const lat = point.geo[0]
    const lng = point.geo[1]

    const icon = L.divIcon({
      html: createMarkerContent(index, point.day, point.checked),
      className: 'custom-marker-container',
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    })

    const marker = L.marker([lat, lng], { icon: icon })

    marker.bindPopup(createPopupContent(point), {
      maxWidth: 280,
      className: 'custom-popup'
    })

    marker.on('click', function() {
      store.selectPoint(point.id)
    })

    marker.addTo(map)
    markers.push(marker)
  })
}

async function updateRoutes() {
  routePolylines.forEach(p => map.removeLayer(p))
  routePolylines = []

  const routeData = libraryItinerary.value
  if (!routeData || routeData.length === 0) return

  let routePlanner
  if (routeType.value === 'walking') {
    routePlanner = planWalkingRoute
  } else if (routeType.value === 'cycling') {
    routePlanner = planCyclingRoute
  } else {
    routePlanner = planDrivingRoute
  }

  for (let dayIndex = 0; dayIndex < routeData.length; dayIndex++) {
    const dayPlan = routeData[dayIndex]
    if (dayPlan.points.length < 2) continue

    const color = dayColors[dayIndex % dayColors.length]

    for (let i = 0; i < dayPlan.points.length - 1; i++) {
      const from = dayPlan.points[i]
      const to = dayPlan.points[i + 1]

      if (!from.geo || !to.geo) continue

      try {
        const route = await routePlanner(
          [from.geo[1], from.geo[0]],
          [to.geo[1], to.geo[0]]
        )

        if (route && route.length > 0) {
          const latlngs = route.map(p => [p.lat, p.lng])
          const polyline = L.polyline(latlngs, {
            color: color,
            weight: 5,
            opacity: 0.8,
            dashArray: '10, 5'
          })
          polyline.addTo(map)
          routePolylines.push(polyline)
        }
      } catch (e) {
        console.warn('路线规划失败，使用直线:', e.message)
        const straightLine = L.polyline([
          [from.geo[0], from.geo[1]],
          [to.geo[0], to.geo[1]]
        ], {
          color: color,
          weight: 3,
          opacity: 0.6,
          dashArray: '5, 5'
        })
        straightLine.addTo(map)
        routePolylines.push(straightLine)
      }
    }
  }
}

function fitBoundsToPoints() {
  if (!map || points.value.length === 0) return

  const validPoints = points.value.filter(p => p.geo && p.geo.length === 2)
  if (validPoints.length === 0) return

  if (validPoints.length === 1) {
    map.setView([validPoints[0].geo[0], validPoints[0].geo[1]], 14)
    return
  }

  const latlngs = validPoints.map(p => [p.geo[0], p.geo[1]])
  map.fitBounds(latlngs, { padding: [40, 40] })
}

function focusPoint(pointId) {
  const point = points.value.find(p => p.id === pointId)
  if (!point || !point.geo || !map) return

  map.setView([point.geo[0], point.geo[1]], 16)

  const markerIndex = points.value.findIndex(p => p.id === pointId)
  if (markerIndex >= 0 && markers[markerIndex]) {
    markers[markerIndex].openPopup()
  }
}

watch(points, function() {
  nextTick(function() {
    updateMarkers()
    if (points.value.length > 0) {
      setTimeout(function() { fitBoundsToPoints() }, 300)
    }
  })
}, { deep: true })

watch(libraryItinerary, async function() {
  nextTick(async function() {
    updateMarkers()
    await updateRoutes()
    if (libraryItinerary.value.length > 0) {
      setTimeout(function() { fitBoundsToPoints() }, 500)
    }
  })
}, { deep: true })

watch(selectedPointId, function(newId) {
  if (newId) {
    focusPoint(newId)
  }
})

watch(defaultCenter, function() {
  if (map && bangumi.value && defaultCenter.value && defaultCenter.value.length === 2) {
    map.setView([defaultCenter.value[0], defaultCenter.value[1]], defaultZoom.value || 10)
  }
})

watch(coordinateLibrary, function() {
  points.value.forEach(function(point, index) {
    if (markers[index]) {
      const popup = markers[index].getPopup()
      if (popup) {
        popup.setContent(createPopupContent(point))
      }
    }
  })
}, { deep: true })

onMounted(function() {
  nextTick(function() {
    setTimeout(function() {
      initMap()
    }, 100)
  })
})

onBeforeUnmount(function() {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.map-container {
  flex: 1;
  position: relative;
  height: 100%;
}

.map-element {
  width: 100%;
  height: 100%;
}

.map-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  z-index: 1000;
  background: rgba(26, 26, 46, 0.8);
  padding: 20px 30px;
  border-radius: 8px;
}

:deep(.custom-marker-container) {
  background: transparent !important;
  border: none !important;
}

:deep(.custom-marker) {
  transition: transform 0.2s ease;
}

:deep(.custom-marker:hover) {
  transform: scale(1.15);
}

:deep(.custom-popup .leaflet-popup-content-wrapper) {
  background: #1e2a4a;
  color: #e0e0e0;
  border-radius: 8px;
  padding: 0;
}

:deep(.custom-popup .leaflet-popup-content) {
  margin: 0;
}

:deep(.custom-popup .leaflet-popup-tip) {
  background: #1e2a4a;
}

:deep(.landmark-popup) {
  min-width: 180px;
  max-width: 260px;
  padding: 12px;
}

:deep(.popup-title) {
  font-size: 15px;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 8px;
}

:deep(.popup-image) {
  width: 100%;
  max-height: 160px;
  object-fit: cover;
  border-radius: 6px;
  margin-bottom: 8px;
}

:deep(.popup-info) {
  display: flex;
  gap: 10px;
  font-size: 13px;
  color: #a0a0a0;
}

:deep(.popup-day) {
  color: #409EFF;
  font-weight: 500;
}

:deep(.popup-origin) {
  margin-top: 6px;
  font-size: 11px;
  color: #a0a0a0;
}

:deep(.popup-origin a) {
  color: #409EFF;
  text-decoration: none;
}

:deep(.popup-footer) {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

:deep(.popup-library-btn) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: transparent;
  color: #a0a0a0;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

:deep(.popup-library-btn:hover) {
  background: rgba(64, 158, 255, 0.15);
  border-color: rgba(64, 158, 255, 0.4);
  color: #409EFF;
}

:deep(.popup-library-btn.is-added) {
  background: rgba(255, 215, 0, 0.2);
  color: #FFD700;
  border-color: rgba(255, 215, 0, 0.4);
}
</style>
