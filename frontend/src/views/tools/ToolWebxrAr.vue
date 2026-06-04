<template>
  <div class="page">
    <video ref="videoRef" autoplay playsinline></video>
    <canvas ref="canvasRef" @click="onCanvasClick" @mousedown="onCanvasMouseDown" @mousemove="onCanvasMouseMove" @mouseup="onCanvasMouseUp" @wheel="onCanvasWheel"></canvas>

    <div class="ar-badge" v-show="isRunning">AR 模式运行中</div>

    <div class="sidebar">
      <router-link to="/camera">&larr; 返回工具集</router-link>
      <h2>WebXR AR 应用</h2>

      <div class="setting-group">
        <label>3D 模型</label>
        <div class="model-grid">
          <div
            v-for="m in modelOptions"
            :key="m.id"
            :class="['model-btn', { active: currentModel === m.id }]"
            @click="currentModel = m.id"
          >
            <span class="icon">{{ m.icon }}</span>{{ m.label }}
          </div>
        </div>
      </div>

      <div class="setting-group">
        <label>模型大小: {{ modelScaleDisplay }}</label>
        <input type="range" min="20" max="300" :value="modelScaleRaw" @input="onScaleChange" />
      </div>

      <div class="setting-group">
        <label>模型颜色</label>
        <select :value="modelColor" @change="modelColor = $event.target.value">
          <option value="#4caf50">绿色</option>
          <option value="#2196f3">蓝色</option>
          <option value="#f44336">红色</option>
          <option value="#ffeb3b">黄色</option>
          <option value="#9c27b0">紫色</option>
          <option value="#ff9800">橙色</option>
          <option value="#ffffff">白色</option>
        </select>
      </div>

      <div class="setting-group">
        <label>放置位置</label>
        <div style="display:flex;gap:6px;">
          <button @click="placeModel(0, 0, 0)">中间</button>
          <button @click="placeModel(-2, 0.5, 0)">左侧</button>
          <button @click="placeModel(2, 0.5, 0)">右侧</button>
        </div>
      </div>

      <div ref="cameraSelectorContainer"></div>

      <div class="controls">
        <button class="primary" @click="toggleCamera">{{ isRunning ? '关闭摄像头' : '开启摄像头' }}</button>
        <button @click="takePhoto">拍照</button>
        <button @click="clearModels">清除模型</button>
      </div>

      <div class="info">
        <strong>操作说明:</strong><br />
        - 点击画布放置模型<br />
        - 拖拽旋转视角<br />
        - 滚轮缩放<br />
        - 支持 WebXR 的设备可进入沉浸式 AR 模式
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useCamera } from '../../composables/useCamera.js'

const { stream, isRunning, startCamera, stopCamera, initCameraSelector, getSelectedStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const cameraSelectorContainer = ref(null)

const modelOptions = [
  { id: 'cube', icon: '🧊', label: '方块' },
  { id: 'sphere', icon: '🔮', label: '球体' },
  { id: 'pyramid', icon: '🔺', label: '金字塔' },
  { id: 'torus', icon: '🍩', label: '环面' },
  { id: 'robot', icon: '🤖', label: '机器人' },
  { id: 'tree', icon: '🌲', label: '树木' }
]

const currentModel = ref('cube')
const modelScaleRaw = ref(100)
const modelScaleDisplay = ref('1.0')
const modelColor = ref('#4caf50')

let THREE = null
let scene = null
let camera = null
let renderer = null
let videoMesh = null
let models = []
let animId = null
let localStream = null

const raycaster = { setFromCamera: null }
let mouse = null
let plane = null
let isDragging = false
let lastMouse = { x: 0, y: 0 }
let cameraAngle = 0
let cameraHeight = 3

function onScaleChange(e) {
  modelScaleRaw.value = parseInt(e.target.value)
  modelScaleDisplay.value = (modelScaleRaw.value / 100).toFixed(1)
}

function createModel(type, position) {
  const color = new THREE.Color(modelColor.value)
  const s = modelScaleRaw.value / 100
  const material = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.2,
    roughness: 0.7
  })

  const group = new THREE.Group()

  switch (type) {
    case 'cube': {
      const geometry = new THREE.BoxGeometry(s, s, s)
      group.add(new THREE.Mesh(geometry, material))
      break
    }
    case 'sphere': {
      const geometry = new THREE.SphereGeometry(s * 0.5, 32, 32)
      group.add(new THREE.Mesh(geometry, material))
      break
    }
    case 'pyramid': {
      const geometry = new THREE.ConeGeometry(s * 0.5, s, 4)
      group.add(new THREE.Mesh(geometry, material))
      break
    }
    case 'torus': {
      const geometry = new THREE.TorusGeometry(s * 0.4, s * 0.15, 16, 32)
      group.add(new THREE.Mesh(geometry, material))
      break
    }
    case 'robot': {
      const body = new THREE.Mesh(new THREE.BoxGeometry(s * 0.6, s * 0.8, s * 0.4), material)
      body.position.y = s * 0.4
      group.add(body)
      const head = new THREE.Mesh(new THREE.BoxGeometry(s * 0.4, s * 0.4, s * 0.35), material)
      head.position.y = s * 1
      group.add(head)
      const eyeMat = new THREE.MeshBasicMaterial({ color: 0x00ffff })
      const eyeL = new THREE.Mesh(new THREE.SphereGeometry(s * 0.05), eyeMat)
      eyeL.position.set(-s * 0.1, s * 1.05, s * 0.18)
      group.add(eyeL)
      const eyeR = eyeL.clone()
      eyeR.position.x = s * 0.1
      group.add(eyeR)
      const armL = new THREE.Mesh(new THREE.BoxGeometry(s * 0.15, s * 0.6, s * 0.15), material)
      armL.position.set(-s * 0.45, s * 0.4, 0)
      group.add(armL)
      const armR = armL.clone()
      armR.position.x = s * 0.45
      group.add(armR)
      const legL = new THREE.Mesh(new THREE.BoxGeometry(s * 0.2, s * 0.5, s * 0.2), material)
      legL.position.set(-s * 0.15, -s * 0.25, 0)
      group.add(legL)
      const legR = legL.clone()
      legR.position.x = s * 0.15
      group.add(legR)
      break
    }
    case 'tree': {
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(s * 0.08, s * 0.1, s * 0.6), new THREE.MeshStandardMaterial({ color: 0x8d6e63 }))
      trunk.position.y = s * 0.3
      group.add(trunk)
      const foliage = new THREE.Mesh(new THREE.ConeGeometry(s * 0.4, s * 0.8, 8), material)
      foliage.position.y = s * 0.9
      group.add(foliage)
      const foliage2 = new THREE.Mesh(new THREE.ConeGeometry(s * 0.3, s * 0.6, 8), material)
      foliage2.position.y = s * 1.3
      group.add(foliage2)
      break
    }
  }

  group.position.copy(position)
  group.castShadow = true
  scene.add(group)
  models.push(group)
  return group
}

function placeModel(x, y, z) {
  createModel(currentModel.value, new THREE.Vector3(x, y, z))
}

function initThree() {
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100)
  camera.position.set(0, 3, 5)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true, alpha: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true

  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(5, 10, 5)
  dirLight.castShadow = true
  scene.add(dirLight)

  const groundGeo = new THREE.PlaneGeometry(20, 20)
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0x333333,
    transparent: true,
    opacity: 0.3
  })
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.receiveShadow = true
  scene.add(ground)

  const grid = new THREE.GridHelper(20, 20, 0x444444, 0x222222)
  grid.material.transparent = true
  grid.material.opacity = 0.3
  scene.add(grid)

  createVideoBackground()
}

function createVideoBackground() {
  const videoTexture = new THREE.VideoTexture(videoRef.value)
  videoTexture.minFilter = THREE.LinearFilter

  const bgGeo = new THREE.PlaneGeometry(16, 9)
  const bgMat = new THREE.MeshBasicMaterial({ map: videoTexture, side: THREE.DoubleSide })
  videoMesh = new THREE.Mesh(bgGeo, bgMat)
  videoMesh.position.set(0, 2, -5)
  scene.add(videoMesh)
}

function animate() {
  animId = requestAnimationFrame(animate)

  if (videoMesh && localStream) {
    videoMesh.material.map.needsUpdate = true
  }

  models.forEach((m) => {
    m.rotation.y += 0.005
    m.children.forEach(child => {
      if (child.isMesh) child.castShadow = true
    })
  })

  renderer.render(scene, camera)
}

function onCanvasClick(e) {
  if (!localStream) return
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const intersectPoint = new THREE.Vector3()
  raycaster.ray.intersectPlane(plane, intersectPoint)

  if (intersectPoint) {
    createModel(currentModel.value, intersectPoint)
  }
}

function onCanvasMouseDown(e) {
  isDragging = true
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onCanvasMouseMove(e) {
  if (!isDragging) return
  cameraAngle -= (e.clientX - lastMouse.x) * 0.005
  cameraHeight = Math.max(1, Math.min(10, cameraHeight + (e.clientY - lastMouse.y) * 0.02))
  camera.position.x = Math.sin(cameraAngle) * 5
  camera.position.z = Math.cos(cameraAngle) * 5
  camera.position.y = cameraHeight
  camera.lookAt(0, 0, 0)
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onCanvasMouseUp() {
  isDragging = false
}

function onCanvasWheel(e) {
  const dist = camera.position.length()
  const newDist = Math.max(2, Math.min(15, dist + e.deltaY * 0.01))
  camera.position.normalize().multiplyScalar(newDist)
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
      if (models.length === 0) {
        createModel('cube', new THREE.Vector3(0, 0.5, 0))
      }
    } catch (e) {
      console.error(e)
    }
  }
}

function takePhoto() {
  renderer.render(scene, camera)
  const link = document.createElement('a')
  link.download = 'ar_' + Date.now() + '.png'
  link.href = canvasRef.value.toDataURL()
  link.click()
}

function clearModels() {
  models.forEach(m => scene.remove(m))
  models = []
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

onMounted(async () => {
  await nextTick()
  THREE = await import('https://cdn.jsdelivr.net/npm/three@latest/build/three.module.js')
  const THREE_NS = THREE

  mouse = new THREE_NS.Vector2()
  plane = new THREE_NS.Plane(new THREE_NS.Vector3(0, 1, 0), 0)

  raycaster.setFromCamera = (m, cam) => {
    const rc = new THREE_NS.Raycaster()
    rc.setFromCamera(m, cam)
    raycaster.ray = rc.ray
  }

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

.model-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }

.model-btn {
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

.model-btn:hover { border-color: #444; }
.model-btn.active { border-color: #667eea; background: #1a1a3a; color: #fff; }
.model-btn .icon { font-size: 20px; display: block; margin-bottom: 2px; }

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

.ar-badge {
  position: fixed;
  top: 12px;
  left: 276px;
  background: rgba(76,175,80,0.8);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  z-index: 10;
}
</style>
