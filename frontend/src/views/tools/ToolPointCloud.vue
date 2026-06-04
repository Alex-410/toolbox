<template>
  <div class="page">
    <video ref="videoRef" autoplay playsinline></video>
    <canvas
      ref="canvasRef"
      @mousedown="onCanvasMouseDown"
      @mousemove="onCanvasMouseMove"
      @mouseup="onCanvasMouseUp"
      @wheel="onCanvasWheel"
    ></canvas>

    <div class="sidebar">
      <router-link to="/camera">&larr; 返回工具集</router-link>
      <h2>3D 点云可视化</h2>

      <div class="setting-group">
        <label>点云密度: {{ density }}</label>
        <input type="range" min="32" max="256" :value="density" step="16" @input="density = +$event.target.value" />
      </div>

      <div class="setting-group">
        <label>深度缩放: {{ depthScale.toFixed(1) }}</label>
        <input type="range" min="10" max="80" :value="depthScaleRaw" @input="onDepthScaleChange" />
      </div>

      <div class="setting-group">
        <label>点大小: {{ pointSize }}</label>
        <input type="range" min="1" max="8" :value="pointSize" @input="pointSize = +$event.target.value" />
      </div>

      <div class="setting-group">
        <label>色彩模式</label>
        <select v-model="colorMode">
          <option value="rgb">原始色彩</option>
          <option value="depth">深度热力图</option>
          <option value="grayscale">灰度</option>
          <option value="neon">霓虹</option>
        </select>
      </div>

      <div class="setting-group">
        <label>深度算法</label>
        <select v-model="depthAlgo">
          <option value="luminance">亮度作为深度</option>
          <option value="edge">边缘检测</option>
          <option value="center">中心距离</option>
        </select>
      </div>

      <div class="setting-group">
        <label>视图模式</label>
        <select v-model="viewMode">
          <option value="orbit">自由旋转</option>
          <option value="front">正面</option>
          <option value="top">俯视</option>
          <option value="auto">自动旋转</option>
        </select>
      </div>

      <div ref="cameraSelectorContainer"></div>

      <div class="controls">
        <button class="primary" @click="toggleCamera">{{ isRunning ? '关闭摄像头' : '开启摄像头' }}</button>
        <button @click="takePhoto">拍照</button>
        <button @click="exportPointCloud">导出点云</button>
      </div>

      <div class="info">
        <strong>操作说明:</strong><br />
        - 拖拽旋转视角<br />
        - 滚轮缩放<br />
        - 亮度/边缘/中心距离模拟深度
      </div>
    </div>

    <div class="preview-mini" v-show="isRunning" ref="miniPreviewContainer"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useCamera } from '../../composables/useCamera.js'

const { stream, isRunning, startCamera, stopCamera, initCameraSelector, getSelectedStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const cameraSelectorContainer = ref(null)
const miniPreviewContainer = ref(null)

const density = ref(128)
const depthScaleRaw = ref(20)
const depthScale = ref(2.0)
const pointSize = ref(2)
const colorMode = ref('rgb')
const depthAlgo = ref('luminance')
const viewMode = ref('orbit')

let THREE = null
let scene = null
let camera = null
let renderer = null
let pointCloud = null
let animId = null
let localStream = null
let points = []

const processCanvas = document.createElement('canvas')
const processCtx = processCanvas.getContext('2d', { willReadFrequently: true })

let previewCanvas = null
let previewCtx = null

let isDragging = false
let lastMouse = { x: 0, y: 0 }

function onDepthScaleChange(e) {
  depthScaleRaw.value = parseInt(e.target.value)
  depthScale.value = depthScaleRaw.value / 10
}

function initThree() {
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100)
  camera.position.set(0, 0, 4)

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x000000)

  const axes = new THREE.AxesHelper(2)
  axes.material.transparent = true
  axes.material.opacity = 0.3
  scene.add(axes)
}

function updatePointCloud() {
  if (!localStream || !videoRef.value.videoWidth) return

  const w = density.value
  const h = Math.floor(density.value * videoRef.value.videoHeight / videoRef.value.videoWidth)
  processCanvas.width = w
  processCanvas.height = h

  processCtx.save()
  processCtx.translate(w, 0)
  processCtx.scale(-1, 1)
  processCtx.drawImage(videoRef.value, 0, 0, w, h)
  processCtx.restore()

  const imageData = processCtx.getImageData(0, 0, w, h)
  const pixels = imageData.data

  previewCanvas.width = w
  previewCanvas.height = h
  previewCtx.putImageData(imageData, 0, 0)

  if (pointCloud) {
    scene.remove(pointCloud)
    pointCloud.geometry.dispose()
    pointCloud.material.dispose()
  }

  const positions = []
  const colors = []

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4
      const r = pixels[idx] / 255
      const g = pixels[idx + 1] / 255
      const b = pixels[idx + 2] / 255

      let depth
      if (depthAlgo.value === 'luminance') {
        depth = (r * 0.299 + g * 0.587 + b * 0.114)
      } else if (depthAlgo.value === 'edge') {
        let edgeX = 0, edgeY = 0
        if (x > 0 && x < w - 1) {
          const left = (y * w + x - 1) * 4
          const right = (y * w + x + 1) * 4
          edgeX = Math.abs(pixels[idx] - pixels[left]) + Math.abs(pixels[idx] - pixels[right])
        }
        if (y > 0 && y < h - 1) {
          const up = ((y - 1) * w + x) * 4
          const down = ((y + 1) * w + x) * 4
          edgeY = Math.abs(pixels[idx] - pixels[up]) + Math.abs(pixels[idx] - pixels[down])
        }
        depth = Math.min(1, (edgeX + edgeY) / 512)
      } else {
        const cx = (x / w - 0.5) * 2
        const cy = (y / h - 0.5) * 2
        depth = 1 - Math.sqrt(cx * cx + cy * cy) * 0.5
      }

      const px = (x / w - 0.5) * 4
      const py = -(y / h - 0.5) * 4 * (h / w)
      const pz = -depth * depthScale.value

      positions.push(px, py, pz)

      let cr, cg, cb
      if (colorMode.value === 'rgb') {
        cr = r; cg = g; cb = b
      } else if (colorMode.value === 'depth') {
        const t = depth
        cr = Math.min(1, t * 2)
        cg = Math.min(1, t < 0.5 ? t * 2 : 2 - t * 2)
        cb = Math.min(1, (1 - t) * 2)
      } else if (colorMode.value === 'grayscale') {
        cr = depth; cg = depth; cb = depth
      } else {
        cr = Math.sin(depth * Math.PI) * 0.5 + 0.5
        cg = Math.sin(depth * Math.PI + 2) * 0.5 + 0.5
        cb = Math.sin(depth * Math.PI + 4) * 0.5 + 0.5
      }
      colors.push(cr, cg, cb)
    }
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))

  const material = new THREE.PointsMaterial({
    size: pointSize.value / 100,
    vertexColors: true,
    sizeAttenuation: true
  })

  pointCloud = new THREE.Points(geometry, material)
  scene.add(pointCloud)

  points = positions
}

function animate() {
  animId = requestAnimationFrame(animate)

  if (viewMode.value === 'auto') {
    scene.rotation.y += 0.003
  }

  updatePointCloud()
  renderer.render(scene, camera)
}

function onCanvasMouseDown(e) {
  isDragging = true
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onCanvasMouseMove(e) {
  if (!isDragging) return
  scene.rotation.y += (e.clientX - lastMouse.x) * 0.005
  scene.rotation.x += (e.clientY - lastMouse.y) * 0.005
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onCanvasMouseUp() {
  isDragging = false
}

function onCanvasWheel(e) {
  camera.position.z = Math.max(1, Math.min(10, camera.position.z + e.deltaY * 0.01))
}

async function toggleCamera() {
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
    localStream = null
    videoRef.value.srcObject = null
    isRunning.value = false
  } else {
    try {
      localStream = await getSelectedStream()
      videoRef.value.srcObject = localStream
      await videoRef.value.play()
      isRunning.value = true
    } catch (e) {
      console.error(e)
    }
  }
}

function takePhoto() {
  renderer.render(scene, camera)
  const link = document.createElement('a')
  link.download = 'pointcloud_' + Date.now() + '.png'
  link.href = canvasRef.value.toDataURL()
  link.click()
}

function exportPointCloud() {
  if (points.length === 0) return
  let obj = '# Point Cloud Export\n'
  for (let i = 0; i < points.length; i += 3) {
    obj += `v ${points[i].toFixed(4)} ${points[i + 1].toFixed(4)} ${points[i + 2].toFixed(4)}\n`
  }
  const blob = new Blob([obj], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'pointcloud.obj'
  a.click()
  URL.revokeObjectURL(url)
}

async function onCameraSwitch() {
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
    localStream = await getSelectedStream()
    videoRef.value.srcObject = localStream
  }
}

function onResize() {
  if (camera && renderer) {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
  }
}

watch(viewMode, (val) => {
  if (!scene || !camera) return
  scene.rotation.set(0, 0, 0)
  if (val === 'front') {
    camera.position.set(0, 0, 4)
  } else if (val === 'top') {
    camera.position.set(0, 4, 0.01)
    camera.lookAt(0, 0, 0)
  } else {
    camera.position.set(0, 0, 4)
  }
})

onMounted(async () => {
  await nextTick()

  previewCanvas = document.createElement('canvas')
  previewCanvas.style.cssText = 'width:100%;height:100%;object-fit:cover;'
  previewCtx = previewCanvas.getContext('2d')
  miniPreviewContainer.value.appendChild(previewCanvas)

  THREE = await import('https://cdn.jsdelivr.net/npm/three@latest/build/three.module.js')

  initThree()
  animate()

  window.addEventListener('resize', onResize)
  initCameraSelector(cameraSelectorContainer.value, onCameraSwitch)
})

onUnmounted(() => {
  if (animId) {
    cancelAnimationFrame(animId)
    animId = null
  }
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
    localStream = null
  }
  if (pointCloud) {
    scene.remove(pointCloud)
    pointCloud.geometry.dispose()
    pointCloud.material.dispose()
    pointCloud = null
  }
  if (renderer) {
    renderer.dispose()
    renderer = null
  }
  if (scene) {
    scene.traverse(obj => {
      if (obj.geometry) obj.geometry.dispose()
      if (obj.material) {
        if (Array.isArray(obj.material)) {
          obj.material.forEach(m => m.dispose())
        } else {
          obj.material.dispose()
        }
      }
    })
    scene = null
  }
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
* { margin: 0; padding: 0; box-sizing: border-box; }

.page {
  font-family: -apple-system, sans-serif;
  background: #000;
  color: #e0e0e0;
  overflow: hidden;
  height: 100vh;
  width: 100vw;
  position: relative;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

video { display: none; }

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 260px;
  height: 100%;
  background: rgba(10,10,10,0.9);
  border-right: 1px solid #222;
  padding: 16px;
  overflow-y: auto;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 12px;
  backdrop-filter: blur(8px);
}

.sidebar h2 { font-size: 16px; }
.sidebar a { color: #667eea; text-decoration: none; font-size: 13px; }

button {
  padding: 8px 16px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 13px;
  cursor: pointer;
}

button:hover { background: #2a2a2a; }
button.primary { background: #1a73e8; border-color: #1a73e8; }

.controls { display: flex; gap: 8px; flex-wrap: wrap; }

.setting-group { display: flex; flex-direction: column; gap: 4px; }
.setting-group label { font-size: 12px; color: #888; }

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

select {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e0e0e0;
  padding: 6px;
  font-size: 13px;
}

.info {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 12px;
  font-size: 11px;
  color: #666;
  line-height: 1.6;
}

.preview-mini {
  position: fixed;
  bottom: 16px;
  right: 16px;
  width: 200px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #333;
  z-index: 10;
}
</style>
