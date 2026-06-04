<template>
  <div class="distortion-root">
    <video ref="videoRef" autoplay playsinline style="display:none;"></video>
    <canvas ref="canvasRef" class="three-canvas"></canvas>

    <div class="sidebar">
      <router-link to="/camera" class="back-link">&larr; 返回工具集</router-link>
      <h2>3D 扭曲相机</h2>

      <div class="setting-group">
        <label>几何体</label>
        <div class="geo-grid" @click="onGeoClick">
          <div class="geo-btn" :class="{ active: currentGeo === 'sphere' }" data-geo="sphere"><span class="icon">🔮</span>球体</div>
          <div class="geo-btn" :class="{ active: currentGeo === 'torus' }" data-geo="torus"><span class="icon">🍩</span>环面</div>
          <div class="geo-btn" :class="{ active: currentGeo === 'wave' }" data-geo="wave"><span class="icon">🌊</span>波浪</div>
          <div class="geo-btn" :class="{ active: currentGeo === 'cylinder' }" data-geo="cylinder"><span class="icon">🪣</span>圆柱</div>
          <div class="geo-btn" :class="{ active: currentGeo === 'cone' }" data-geo="cone"><span class="icon">🔺</span>圆锥</div>
          <div class="geo-btn" :class="{ active: currentGeo === 'knot' }" data-geo="knot"><span class="icon">🪢</span>扭结</div>
        </div>
      </div>

      <div class="setting-group">
        <label>变形强度: <span>{{ distortAmountText }}</span></label>
        <input type="range" min="0" max="100" :value="distortAmountSlider" @input="onDistortAmountInput">
      </div>

      <div class="setting-group">
        <label>变形速度: <span>{{ distortSpeedText }}</span></label>
        <input type="range" min="0" max="300" :value="distortSpeedSlider" @input="onDistortSpeedInput">
      </div>

      <div class="setting-group">
        <label>细分级别: <span>{{ subdivisionText }}</span></label>
        <input type="range" min="8" max="64" :value="subdivisionSlider" step="8" @input="onSubdivisionInput">
      </div>

      <div class="setting-group">
        <label>自动旋转</label>
        <select v-model="autoRotate" class="setting-select">
          <option value="on">开启</option>
          <option value="off">关闭</option>
        </select>
      </div>

      <div ref="cameraSelectorContainer" id="cameraSelectorContainer"></div>

      <div class="controls">
        <button class="btn primary" @click="toggleCamera">{{ cameraBtnText }}</button>
        <button class="btn" @click="takePhoto">拍照</button>
        <button class="btn" @click="toggleFullscreen">全屏</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@latest/build/three.module.js'
import { useCamera } from '../../composables/useCamera.js'

const { initCameraSelector, getSelectedStream, stream: cameraStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const cameraSelectorContainer = ref(null)

const currentGeo = ref('sphere')
const distortAmountText = ref('0.30')
const distortSpeedText = ref('1.0')
const subdivisionText = ref('32')
const distortAmountSlider = ref(30)
const distortSpeedSlider = ref(100)
const subdivisionSlider = ref(32)
const autoRotate = ref('on')
const cameraBtnText = ref('开启摄像头')

let stream = null
let scene = null
let camera = null
let renderer = null
let mesh = null
let videoTexture = null
let distortAmount = 0.3
let distortSpeed = 1.0
let subdivision = 32
let animId = null
let isDragging = false
let lastMouse = { x: 0, y: 0 }

function handleMousedown(e) {
  isDragging = true
  lastMouse = { x: e.clientX, y: e.clientY }
}

function handleMousemove(e) {
  if (!isDragging || !mesh) return
  mesh.rotation.y += (e.clientX - lastMouse.x) * 0.005
  mesh.rotation.x += (e.clientY - lastMouse.y) * 0.005
  lastMouse = { x: e.clientX, y: e.clientY }
}

function handleMouseup() {
  isDragging = false
}

function handleWheel(e) {
  if (!camera) return
  camera.position.z = Math.max(1.5, Math.min(8, camera.position.z + e.deltaY * 0.005))
}

function handleResize() {
  if (camera && renderer) {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
  }
}

function initThree() {
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100)
  camera.position.z = 3

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true, alpha: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

  const ambient = new THREE.AmbientLight(0xffffff, 0.8)
  scene.add(ambient)
  const dir = new THREE.DirectionalLight(0xffffff, 0.5)
  dir.position.set(2, 2, 3)
  scene.add(dir)

  createGeometry()
}

function createGeometry() {
  if (mesh) scene.remove(mesh)

  let geometry
  switch (currentGeo.value) {
    case 'sphere':
      geometry = new THREE.SphereGeometry(1, subdivision, subdivision)
      break
    case 'torus':
      geometry = new THREE.TorusGeometry(0.8, 0.35, subdivision, subdivision)
      break
    case 'wave':
      geometry = new THREE.PlaneGeometry(3, 3, subdivision, subdivision)
      break
    case 'cylinder':
      geometry = new THREE.CylinderGeometry(0.8, 0.8, 1.5, subdivision, subdivision)
      break
    case 'cone':
      geometry = new THREE.ConeGeometry(0.8, 1.5, subdivision, subdivision)
      break
    case 'knot':
      geometry = new THREE.TorusKnotGeometry(0.6, 0.25, subdivision * 3, subdivision)
      break
    default:
      geometry = new THREE.SphereGeometry(1, subdivision, subdivision)
  }

  const posAttr = geometry.getAttribute('position')
  const origPositions = new Float32Array(posAttr.array.length)
  origPositions.set(posAttr.array)
  geometry.userData.origPositions = origPositions

  const material = new THREE.MeshStandardMaterial({
    map: videoTexture || null,
    side: THREE.DoubleSide,
    metalness: 0.1,
    roughness: 0.8
  })

  mesh = new THREE.Mesh(geometry, material)
  scene.add(mesh)
}

function distortGeometry(time) {
  if (!mesh) return
  const geometry = mesh.geometry
  const posAttr = geometry.getAttribute('position')
  const orig = geometry.userData.origPositions

  for (let i = 0; i < posAttr.count; i++) {
    const ox = orig[i * 3]
    const oy = orig[i * 3 + 1]
    const oz = orig[i * 3 + 2]

    let dx = 0, dy = 0, dz = 0
    const t = time * distortSpeed

    switch (currentGeo.value) {
      case 'sphere':
      case 'cylinder':
      case 'cone': {
        const noise = Math.sin(ox * 3 + t) * Math.cos(oy * 3 + t * 0.7) * Math.sin(oz * 3 + t * 1.3)
        const r = Math.sqrt(ox * ox + oy * oy + oz * oz) || 1
        dx = (ox / r) * noise * distortAmount
        dy = (oy / r) * noise * distortAmount
        dz = (oz / r) * noise * distortAmount
        break
      }
      case 'torus':
      case 'knot': {
        const n2 = Math.sin(ox * 5 + t) * Math.cos(oy * 5 + t * 0.8)
        dx = n2 * distortAmount * 0.5
        dy = Math.sin(oz * 4 + t * 1.2) * distortAmount * 0.5
        dz = n2 * distortAmount * 0.3
        break
      }
      case 'wave': {
        const wave = Math.sin(ox * 2 + t) * Math.cos(oy * 2 + t * 0.6)
        dz = wave * distortAmount
        break
      }
    }

    posAttr.setXYZ(i, ox + dx, oy + dy, oz + dz)
  }

  posAttr.needsUpdate = true
  geometry.computeVertexNormals()
}

function animate() {
  animId = requestAnimationFrame(animate)
  const time = performance.now() * 0.001

  if (videoTexture && stream) {
    videoTexture.needsUpdate = true
  }

  distortGeometry(time)

  if (autoRotate.value === 'on' && mesh) {
    mesh.rotation.y += 0.003
    mesh.rotation.x += 0.001
  }

  renderer.render(scene, camera)
}

async function startCameraFn() {
  try {
    stream = await getSelectedStream()
    videoRef.value.srcObject = stream
    await videoRef.value.play()

    videoTexture = new THREE.VideoTexture(videoRef.value)
    videoTexture.minFilter = THREE.LinearFilter
    videoTexture.magFilter = THREE.LinearFilter

    if (!scene) {
      initThree()
    } else {
      createGeometry()
    }

    cameraBtnText.value = '关闭摄像头'
  } catch (e) {
    console.error(e)
  }
}

function stopCameraFn() {
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null }
  if (animId) { cancelAnimationFrame(animId); animId = null }
  videoRef.value.srcObject = null
  cameraBtnText.value = '开启摄像头'
}

function toggleCamera() {
  if (stream) stopCameraFn()
  else startCameraFn()
}

function takePhoto() {
  renderer.render(scene, camera)
  const link = document.createElement('a')
  link.download = 'distortion_' + Date.now() + '.png'
  link.href = canvasRef.value.toDataURL()
  link.click()
}

function toggleFullscreen() {
  if (document.fullscreenElement) document.exitFullscreen()
  else document.body.requestFullscreen()
}

function onGeoClick(e) {
  const btn = e.target.closest('.geo-btn')
  if (!btn) return
  currentGeo.value = btn.dataset.geo
  if (scene) createGeometry()
}

function onDistortAmountInput(e) {
  distortAmountSlider.value = parseInt(e.target.value)
  distortAmount = distortAmountSlider.value / 100
  distortAmountText.value = distortAmount.toFixed(2)
}

function onDistortSpeedInput(e) {
  distortSpeedSlider.value = parseInt(e.target.value)
  distortSpeed = distortSpeedSlider.value / 100
  distortSpeedText.value = distortSpeed.toFixed(1)
}

function onSubdivisionInput(e) {
  subdivisionSlider.value = parseInt(e.target.value)
  subdivision = subdivisionSlider.value
  subdivisionText.value = subdivision
  if (scene) createGeometry()
}

onMounted(async () => {
  await nextTick()
  canvasRef.value.addEventListener('mousedown', handleMousedown)
  canvasRef.value.addEventListener('mousemove', handleMousemove)
  canvasRef.value.addEventListener('mouseup', handleMouseup)
  canvasRef.value.addEventListener('wheel', handleWheel)
  window.addEventListener('resize', handleResize)
  initCameraSelector(cameraSelectorContainer.value, async () => {
    if (stream) {
      stream.getTracks().forEach(t => t.stop())
      stream = await getSelectedStream()
      videoRef.value.srcObject = stream
    }
  })
  initThree()
  animate()
})

onUnmounted(() => {
  canvasRef.value.removeEventListener('mousedown', handleMousedown)
  canvasRef.value.removeEventListener('mousemove', handleMousemove)
  canvasRef.value.removeEventListener('mouseup', handleMouseup)
  canvasRef.value.removeEventListener('wheel', handleWheel)
  window.removeEventListener('resize', handleResize)
  if (animId) { cancelAnimationFrame(animId); animId = null }
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null }
  if (cameraStream.value) { cameraStream.value.getTracks().forEach(t => t.stop()); cameraStream.value = null }
  if (videoRef.value) videoRef.value.srcObject = null
  if (renderer) { renderer.dispose() }
  if (videoTexture) { videoTexture.dispose() }
})
</script>

<style scoped>
.distortion-root {
  font-family: -apple-system, sans-serif;
  background: #000;
  color: #e0e0e0;
  overflow: hidden;
  height: 100vh;
  width: 100vw;
  position: relative;
}
.three-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
.sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 260px;
  height: 100%;
  background: rgba(10,10,10,0.9);
  border-left: 1px solid #222;
  padding: 16px;
  overflow-y: auto;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 12px;
  backdrop-filter: blur(8px);
}
.sidebar h2 {
  font-size: 16px;
}
.back-link {
  color: #667eea;
  text-decoration: none;
  font-size: 13px;
}
.back-link:hover {
  color: #8b9ff5;
}
.geo-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}
.geo-btn {
  padding: 8px;
  background: #1a1a1a;
  border: 2px solid #2a2a2a;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  font-size: 11px;
  color: #aaa;
  transition: all 0.15s;
}
.geo-btn:hover {
  border-color: #444;
}
.geo-btn.active {
  border-color: #667eea;
  background: #1a1a3a;
  color: #fff;
}
.geo-btn .icon {
  font-size: 20px;
  display: block;
  margin-bottom: 2px;
}
.btn {
  padding: 8px 16px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 13px;
  cursor: pointer;
}
.btn:hover {
  background: #2a2a2a;
}
.btn.primary {
  background: #1a73e8;
  border-color: #1a73e8;
}
.controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.setting-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.setting-group label {
  font-size: 12px;
  color: #888;
}
input[type="range"] {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: #333;
  border: none;
  cursor: pointer;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #667eea;
}
.setting-select {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e0e0e0;
  padding: 6px;
  font-size: 13px;
}
</style>
