<template>
  <div class="gesture-3d">
    <video ref="videoRef" autoplay playsinline style="display:none;"></video>
    <canvas ref="canvasRef"></canvas>

    <div class="gesture-status">
      <div class="gesture-item"><div class="gesture-dot" :class="{ active: leftActive }"></div>左手</div>
      <div class="gesture-item"><div class="gesture-dot" :class="{ active: rightActive }"></div>右手</div>
      <div class="gesture-item" style="color:#888;">{{ gestureText }}</div>
    </div>

    <div class="sidebar">
      <router-link to="/camera">&larr; 返回工具集</router-link>
      <h2>手势控制 3D 模型</h2>

      <div class="setting-group">
        <label>选择模型</label>
        <div class="model-grid" ref="modelGridRef">
          <div v-for="m in models" :key="m.type" class="model-btn" :class="{ active: currentModel === m.type }" :data-model="m.type">
            <span class="icon">{{ m.icon }}</span>{{ m.label }}
          </div>
        </div>
      </div>

      <div ref="cameraSelectorContainer"></div>

      <div class="controls">
        <button class="primary" @click="toggleCamera">{{ cameraBtnText }}</button>
        <button @click="resetModel">重置模型</button>
      </div>

      <div class="info">
        <strong>手势操作:</strong><br>
        ✊ 握拳 = 抓取物体，控制位置<br>
        ✋ 张开手掌 = 推动方向<br>
        🤏 捏合 = 缩放物体<br>
        🤚 左手 = 控制旋转<br>
        <br>
        也可以鼠标拖拽/滚轮操作
      </div>
    </div>

    <div class="hand-preview" v-show="showPreview">
      <canvas ref="handCanvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@latest/build/three.module.js'
import { HandLandmarker, FilesetResolver } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs'
import { useCamera } from '../../composables/useCamera.js'

const { stream, isRunning, startCamera: cameraStart, stopCamera: cameraStop, initCameraSelector, getSelectedStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const handCanvasRef = ref(null)
const cameraSelectorContainer = ref(null)
const modelGridRef = ref(null)

const gestureText = ref('等待手势...')
const leftActive = ref(false)
const rightActive = ref(false)
const cameraBtnText = ref('开启摄像头')
const showPreview = ref(false)
const currentModel = ref('cube')

const models = [
  { type: 'cube', icon: '🧊', label: '方块' },
  { type: 'sphere', icon: '🔮', label: '球体' },
  { type: 'monkey', icon: '🐵', label: '猴头' },
  { type: 'diamond', icon: '💎', label: '钻石' },
  { type: 'star', icon: '⭐', label: '星星' },
  { type: 'heart', icon: '❤️', label: '爱心' }
]

let handLandmarker = null
let localStream = null
let scene, camera, renderer, currentMesh
let animId = null
let leftHand = null
let rightHand = null
let isPinching = false
let lastPinchDist = 0
let isGrabbed = false
let modelPos = new THREE.Vector3(0, 0, 0)
let modelRot = new THREE.Euler(0, 0, 0)
let modelScale = 1
let modelVel = new THREE.Vector3(0, 0, 0)
const DAMPING = 0.88
const MOVE_SPEED = 0.06
const DEADZONE = 0.06
const DETECT_INTERVAL = 50
let lastDetectTime = 0
let lastGestureText = ''
let lastLeftActive = false
let lastRightActive = false
let isDragging = false
let lastMouse = { x: 0, y: 0 }

function initThree() {
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100)
  camera.position.set(0, 1.5, 4)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x0a0a0a)

  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(3, 5, 3)
  scene.add(dirLight)

  const grid = new THREE.GridHelper(10, 10, 0x333333, 0x1a1a1a)
  scene.add(grid)

  createModel(currentModel.value)
}

function createModel(type) {
  if (currentMesh) scene.remove(currentMesh)

  const mat = new THREE.MeshStandardMaterial({
    color: 0x4caf50,
    metalness: 0.3,
    roughness: 0.6
  })

  let geo
  switch (type) {
    case 'cube':
      geo = new THREE.BoxGeometry(1, 1, 1)
      break
    case 'sphere':
      geo = new THREE.SphereGeometry(0.6, 32, 32)
      break
    case 'monkey': {
      const group = new THREE.Group()
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 32), mat)
      group.add(head)
      const earL = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 16), mat)
      earL.position.set(-0.45, 0.25, 0)
      group.add(earL)
      const earR = earL.clone()
      earR.position.x = 0.45
      group.add(earR)
      const nose = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), new THREE.MeshStandardMaterial({ color: 0xffcc80 }))
      nose.position.set(0, -0.05, 0.45)
      group.add(nose)
      const eyeMat = new THREE.MeshBasicMaterial({ color: 0x333333 })
      const eyeL = new THREE.Mesh(new THREE.SphereGeometry(0.06), eyeMat)
      eyeL.position.set(-0.18, 0.1, 0.42)
      group.add(eyeL)
      const eyeR = eyeL.clone()
      eyeR.position.x = 0.18
      group.add(eyeR)
      currentMesh = group
      currentMesh.position.copy(modelPos)
      scene.add(currentMesh)
      return
    }
    case 'diamond':
      geo = new THREE.OctahedronGeometry(0.6)
      mat.color = new THREE.Color(0x42a5f5)
      mat.metalness = 0.8
      mat.roughness = 0.1
      break
    case 'star':
      geo = new THREE.IcosahedronGeometry(0.6)
      mat.color = new THREE.Color(0xffeb3b)
      mat.emissive = new THREE.Color(0x665500)
      break
    case 'heart': {
      const shape = new THREE.Shape()
      shape.moveTo(0, 0)
      shape.bezierCurveTo(0, -0.3, -0.6, -0.3, -0.6, 0)
      shape.bezierCurveTo(-0.6, 0.4, 0, 0.7, 0, 1)
      shape.bezierCurveTo(0, 0.7, 0.6, 0.4, 0.6, 0)
      shape.bezierCurveTo(0.6, -0.3, 0, -0.3, 0, 0)
      geo = new THREE.ExtrudeGeometry(shape, { depth: 0.3, bevelEnabled: true, bevelSize: 0.05 })
      mat.color = new THREE.Color(0xe91e63)
      break
    }
    default:
      geo = new THREE.BoxGeometry(1, 1, 1)
  }

  currentMesh = new THREE.Mesh(geo, mat)
  currentMesh.position.copy(modelPos)
  scene.add(currentMesh)
}

async function initHandLandmarker() {
  const vision = await FilesetResolver.forVisionTasks(
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
  )
  handLandmarker = await HandLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',
      delegate: 'GPU'
    },
    runningMode: 'VIDEO',
    numHands: 2
  })
}

function onMouseDown(e) {
  isDragging = true
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onMouseMove(e) {
  if (!isDragging) return
  modelRot.y += (e.clientX - lastMouse.x) * 0.01
  modelRot.x += (e.clientY - lastMouse.y) * 0.01
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onMouseUp() {
  isDragging = false
}

function onWheel(e) {
  modelScale = Math.max(0.3, Math.min(3, modelScale - e.deltaY * 0.001))
}

function onResize() {
  if (camera && renderer) {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
  }
}

function onModelGridClick(e) {
  const btn = e.target.closest('.model-btn')
  if (!btn) return
  currentModel.value = btn.dataset.model
  createModel(currentModel.value)
}

function toggleCamera() {
  if (localStream) {
    stopCameraLocal()
  } else {
    startCameraLocal()
  }
}

async function startCameraLocal() {
  try {
    localStream = await getSelectedStream()
    videoRef.value.srcObject = localStream

    await new Promise((resolve, reject) => {
      videoRef.value.onloadedmetadata = () => {
        videoRef.value.play().then(resolve).catch(reject)
      }
      videoRef.value.onerror = reject
      setTimeout(() => reject(new Error('视频加载超时')), 10000)
    })

    if (!handLandmarker) await initHandLandmarker()
    showPreview.value = true
    cameraBtnText.value = '关闭摄像头'
  } catch (e) {
    console.error('启动失败:', e)
  }
}

function stopCameraLocal() {
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
    localStream = null
  }
  videoRef.value.srcObject = null
  leftHand = null
  rightHand = null
  showPreview.value = false
  cameraBtnText.value = '开启摄像头'
}

function resetModel() {
  modelPos.set(0, 0, 0)
  modelRot.set(0, 0, 0)
  modelScale = 1
}

function drawHandLandmarks(ctx, landmarks) {
  const connections = [
    [0,1],[1,2],[2,3],[3,4],
    [0,5],[5,6],[6,7],[7,8],
    [0,9],[9,10],[10,11],[11,12],
    [0,13],[13,14],[14,15],[15,16],
    [0,17],[17,18],[18,19],[19,20],
    [5,9],[9,13],[13,17]
  ]

  ctx.strokeStyle = '#4caf50'
  ctx.lineWidth = 1
  for (const [a, b] of connections) {
    ctx.beginPath()
    ctx.moveTo((1 - landmarks[a].x) * 240, landmarks[a].y * 180)
    ctx.lineTo((1 - landmarks[b].x) * 240, landmarks[b].y * 180)
    ctx.stroke()
  }

  for (const lm of landmarks) {
    ctx.beginPath()
    ctx.arc((1 - lm.x) * 240, lm.y * 180, 2, 0, Math.PI * 2)
    ctx.fillStyle = '#fff'
    ctx.fill()
  }
}

function processGestures() {
  let newGestureText = '等待手势...'

  if (rightHand) {
    const thumb = rightHand[4]
    const index = rightHand[8]
    const middle = rightHand[12]
    const ring = rightHand[16]
    const pinky = rightHand[20]
    const wrist = rightHand[0]

    const pinchDist = Math.hypot(thumb.x - index.x, thumb.y - index.y)

    const openFingers = (
      (index.y < rightHand[6].y ? 1 : 0) +
      (middle.y < rightHand[10].y ? 1 : 0) +
      (ring.y < rightHand[14].y ? 1 : 0) +
      (pinky.y < rightHand[18].y ? 1 : 0)
    )

    if (pinchDist < 0.06 && openFingers <= 1) {
      isPinching = true
      if (lastPinchDist > 0) {
        const delta = (pinchDist - lastPinchDist) * 8
        modelScale = Math.max(0.3, Math.min(3, modelScale - delta))
      }
      lastPinchDist = pinchDist
      newGestureText = '🤏 捏合缩放'
    } else {
      isPinching = false
      lastPinchDist = 0
    }

    if (openFingers <= 1 && !isPinching) {
      isGrabbed = true
      const handX = (0.5 - wrist.x) * 4
      const handY = Math.max(0.2, (0.5 - wrist.y) * 3)
      modelPos.x = handX
      modelPos.y = handY
      modelVel.set(0, 0, 0)
      newGestureText = '✊ 握拳 - 控制位置'
    } else if (openFingers >= 3) {
      isGrabbed = false
      const palmX = (wrist.x + rightHand[9].x + rightHand[13].x) / 3
      const palmY = (wrist.y + rightHand[9].y + rightHand[13].y) / 3
      const dx = 0.5 - palmX
      const dy = 0.5 - palmY
      if (Math.abs(dx) > DEADZONE) modelVel.x += dx * MOVE_SPEED
      if (Math.abs(dy) > DEADZONE) modelVel.y += dy * MOVE_SPEED
      const avgZ = (index.z + middle.z + ring.z + pinky.z) / 4 - wrist.z
      if (Math.abs(avgZ) > 0.02) modelVel.z += avgZ * MOVE_SPEED * 2
      newGestureText = '✋ 开掌 - 控制方向'
    }
  }

  if (leftHand) {
    const index = leftHand[8]
    const wrist = leftHand[0]
    const handAngle = Math.atan2(index.y - wrist.y, index.x - wrist.x)
    modelRot.x += (handAngle - modelRot.x) * 0.03
    newGestureText += ' | 🤚 左手旋转'
  }

  if (!isGrabbed) {
    modelPos.x += modelVel.x
    modelPos.y += modelVel.y
    modelPos.z += modelVel.z
    modelVel.multiplyScalar(DAMPING)
    modelPos.x = Math.max(-3, Math.min(3, modelPos.x))
    modelPos.y = Math.max(0, Math.min(3, modelPos.y))
    modelPos.z = Math.max(-2, Math.min(2, modelPos.z))
  }

  if (newGestureText !== lastGestureText) {
    gestureText.value = newGestureText
    lastGestureText = newGestureText
  }
}

function runHandDetection(now) {
  if (videoRef.value.readyState < 2) return

  let results = null
  try {
    results = handLandmarker.detectForVideo(videoRef.value, now)
  } catch (e) {
    return
  }

  const handCtx = handCanvasRef.value.getContext('2d')
  handCtx.save()
  handCtx.translate(240, 0)
  handCtx.scale(-1, 1)
  handCtx.drawImage(videoRef.value, 0, 0, 240, 180)
  handCtx.restore()

  leftHand = null
  rightHand = null

  if (results && results.handedness && results.handedness.length > 0) {
    for (let i = 0; i < results.handedness.length; i++) {
      const label = results.handedness[i][0].categoryName
      const landmarks = results.landmarks[i]

      if (label === 'Left') {
        leftHand = landmarks
      } else {
        rightHand = landmarks
      }
      drawHandLandmarks(handCtx, landmarks)
    }
    processGestures()
  }

  const newLeftActive = leftHand !== null
  const newRightActive = rightHand !== null
  if (newLeftActive !== lastLeftActive) {
    leftActive.value = newLeftActive
    lastLeftActive = newLeftActive
  }
  if (newRightActive !== lastRightActive) {
    rightActive.value = newRightActive
    lastRightActive = newRightActive
  }
}

function animate() {
  animId = requestAnimationFrame(animate)

  if (localStream && handLandmarker) {
    const now = performance.now()
    if (now - lastDetectTime >= DETECT_INTERVAL) {
      lastDetectTime = now
      runHandDetection(now)
    }
  } else {
    if (currentMesh) modelRot.y += 0.005
    if (!isGrabbed) {
      modelVel.multiplyScalar(DAMPING)
      modelPos.x += modelVel.x
      modelPos.y += modelVel.y
      modelPos.z += modelVel.z
    }
  }

  if (currentMesh) {
    currentMesh.position.lerp(modelPos, 0.15)
    currentMesh.rotation.x += (modelRot.x - currentMesh.rotation.x) * 0.1
    currentMesh.rotation.y += (modelRot.y - currentMesh.rotation.y) * 0.1
    currentMesh.scale.setScalar(modelScale)
  }

  renderer.render(scene, camera)
}

function onCameraChange() {
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
    getSelectedStream().then(newStream => {
      localStream = newStream
      videoRef.value.srcObject = localStream
    })
  }
}

onMounted(() => {
  nextTick(() => {
    initCameraSelector(cameraSelectorContainer.value, onCameraChange)
  })

  handCanvasRef.value.width = 240
  handCanvasRef.value.height = 180

  const canvas = canvasRef.value
  canvas.addEventListener('mousedown', onMouseDown)
  canvas.addEventListener('mousemove', onMouseMove)
  canvas.addEventListener('mouseup', onMouseUp)
  canvas.addEventListener('wheel', onWheel)
  modelGridRef.value.addEventListener('click', onModelGridClick)
  window.addEventListener('resize', onResize)

  initThree()
  animate()
})

onUnmounted(() => {
  const canvas = canvasRef.value
  if (canvas) {
    canvas.removeEventListener('mousedown', onMouseDown)
    canvas.removeEventListener('mousemove', onMouseMove)
    canvas.removeEventListener('mouseup', onMouseUp)
    canvas.removeEventListener('wheel', onWheel)
  }
  if (modelGridRef.value) {
    modelGridRef.value.removeEventListener('click', onModelGridClick)
  }
  window.removeEventListener('resize', onResize)

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
  }
  if (scene) {
    scene.traverse(obj => {
      if (obj.geometry) obj.geometry.dispose()
      if (obj.material) obj.material.dispose()
    })
  }
})
</script>

<style scoped>
.gesture-3d {
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
}

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

.sidebar h2 {
  font-size: 16px;
}

.sidebar a {
  color: #667eea;
  text-decoration: none;
  font-size: 13px;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

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

.model-btn:hover {
  border-color: #444;
}

.model-btn.active {
  border-color: #667eea;
  background: #1a1a3a;
  color: #fff;
}

.model-btn .icon {
  font-size: 20px;
  display: block;
  margin-bottom: 2px;
}

button {
  padding: 8px 16px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 13px;
  cursor: pointer;
}

button:hover {
  background: #2a2a2a;
}

button.primary {
  background: #1a73e8;
  border-color: #1a73e8;
}

.controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.info {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 12px;
  font-size: 11px;
  color: #666;
  line-height: 1.6;
}

.gesture-status {
  position: fixed;
  top: 12px;
  left: 276px;
  background: rgba(0,0,0,0.7);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 12px;
  z-index: 10;
  display: flex;
  gap: 16px;
  align-items: center;
}

.gesture-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.gesture-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #555;
}

.gesture-dot.active {
  background: #4caf50;
}

.hand-preview {
  position: fixed;
  bottom: 16px;
  left: 276px;
  width: 240px;
  height: 180px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #333;
  z-index: 10;
}

.hand-preview canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
