<template>
  <div class="pose-skeleton">
    <div class="sidebar">
      <router-link to="/camera">&larr; 返回工具集</router-link>
      <h2>姿势识别 + 3D 骨骼</h2>

      <div id="cameraSelectorContainer" ref="cameraSelectorContainer"></div>

      <div class="setting-group">
        <label>视角</label>
        <select v-model="viewMode">
          <option value="front">正面</option>
          <option value="side">侧面</option>
          <option value="3d">3D 透视</option>
        </select>
      </div>

      <div class="setting-group">
        <label>骨骼样式</label>
        <select v-model="boneStyle">
          <option value="neon">霓虹</option>
          <option value="xray">X光</option>
          <option value="cartoon">卡通</option>
        </select>
      </div>

      <div class="controls">
        <button :class="{ primary: !isRunning }" @click="toggleCamera" :disabled="btnDisabled">
          {{ btnText }}
        </button>
        <button @click="takePhoto">拍照</button>
      </div>

      <div>
        <h3 style="font-size:14px; margin-bottom:8px;">姿势矫正提示</h3>
        <div class="tips-panel" v-html="tipsHtml"></div>
      </div>

      <div style="font-size:11px; color:#555;">{{ fpsText }}</div>
    </div>

    <div class="main">
      <div class="panel">
        <div class="panel-header">摄像头画面</div>
        <div class="panel-body">
          <video ref="videoRef" autoplay playsinline style="display:none;"></video>
          <canvas ref="videoCanvasRef"></canvas>
        </div>
      </div>
      <div class="panel">
        <div class="panel-header">3D 骨骼视图</div>
        <div class="panel-body">
          <canvas ref="skelCanvasRef"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { PoseLandmarker, FilesetResolver } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs'
import { useCamera } from '../../composables/useCamera.js'

const { stream, isRunning, startCamera: cameraStart, stopCamera: cameraStop, initCameraSelector, getSelectedStream } = useCamera()

const videoRef = ref(null)
const videoCanvasRef = ref(null)
const skelCanvasRef = ref(null)
const cameraSelectorContainer = ref(null)

const viewMode = ref('3d')
const boneStyle = ref('neon')
const btnText = ref('开启摄像头')
const btnDisabled = ref(false)
const fpsText = ref('FPS: --')
const tipsHtml = ref('<div class="tip" style="color:#666;">等待检测...</div>')

let poseLandmarker = null
let animId = null
let frameCount = 0
let lastFpsTime = performance.now()
let rotY = 0
let rotX = 0.2
let autoRotate = true
let localStream = null
let isDragging = false
let lastMouse = { x: 0, y: 0 }

const CONNECTIONS = [
  [11,12],[11,13],[13,15],[12,14],[14,16],
  [11,23],[12,24],[23,24],
  [23,25],[25,27],[24,26],[26,28],
  [0,11],[0,12],
  [7,8],[0,7],[0,8],
  [9,10],[0,9],[0,10],
  [1,2],[1,3],[2,4],[3,5],
]

const POSE_LANDMARKS = {
  NOSE: 0, LEFT_EYE_INNER: 1, LEFT_EYE: 2, LEFT_EYE_OUTER: 3,
  RIGHT_EYE_INNER: 4, RIGHT_EYE: 5, RIGHT_EYE_OUTER: 6,
  LEFT_EAR: 7, RIGHT_EAR: 8, MOUTH_LEFT: 9, MOUTH_RIGHT: 10,
  LEFT_SHOULDER: 11, RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13, RIGHT_ELBOW: 14,
  LEFT_WRIST: 15, RIGHT_WRIST: 16,
  LEFT_PINKY: 17, RIGHT_PINKY: 18,
  LEFT_INDEX: 19, RIGHT_INDEX: 20,
  LEFT_THUMB: 21, RIGHT_THUMB: 22,
  LEFT_HIP: 23, RIGHT_HIP: 24,
  LEFT_KNEE: 25, RIGHT_KNEE: 26,
  LEFT_ANKLE: 27, RIGHT_ANKLE: 28,
  LEFT_HEEL: 29, RIGHT_HEEL: 30,
  LEFT_FOOT_INDEX: 31, RIGHT_FOOT_INDEX: 32
}

async function initModel() {
  try {
    const vision = await FilesetResolver.forVisionTasks(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
    )
    const modelCandidates = [
      { path: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task', name: 'full' },
      { path: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task', name: 'lite' },
      { path: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task', name: 'heavy' },
      { path: './models/pose_landmarker_full.task', name: 'local-full' },
      { path: './models/pose_landmarker_lite.task', name: 'local-lite' },
      { path: './models/pose_landmarker_heavy.task', name: 'local-heavy' }
    ]
    for (const model of modelCandidates) {
      try {
        poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: model.path,
            delegate: 'GPU'
          },
          runningMode: 'VIDEO',
          numPoses: 1
        })
        fpsText.value = '模型: ' + model.name
        return true
      } catch (e) {
        console.warn('模型加载失败:', model.name, e.message)
      }
    }
    throw new Error('All model sources failed.')
  } catch (e) {
    console.error(e)
    tipsHtml.value = '<div class="tip tip-err">模型加载失败，请检查网络或代理</div>'
    return false
  }
}

async function startCamera() {
  try {
    btnText.value = '加载中...'
    btnDisabled.value = true

    localStream = await getSelectedStream()
    videoRef.value.srcObject = localStream

    await new Promise((resolve, reject) => {
      videoRef.value.onloadedmetadata = () => {
        videoRef.value.play().then(resolve).catch(reject)
      }
      videoRef.value.onerror = reject
      setTimeout(() => reject(new Error('视频加载超时')), 10000)
    })

    const videoCanvas = videoCanvasRef.value
    const skelCanvas = skelCanvasRef.value
    videoCanvas.width = videoRef.value.videoWidth || 640
    videoCanvas.height = videoRef.value.videoHeight || 480
    skelCanvas.width = 500
    skelCanvas.height = 500

    if (!poseLandmarker) {
      tipsHtml.value = '<div class="tip" style="color:#667eea;">正在加载姿态模型，请稍候...</div>'
      const ok = await initModel()
      if (!ok) {
        btnText.value = '开启摄像头'
        btnDisabled.value = false
        return
      }
    }

    isRunning.value = true
    btnText.value = '关闭摄像头'
    btnDisabled.value = false
    lastFpsTime = performance.now()
    frameCount = 0
    processFrame()
  } catch (e) {
    console.error('启动摄像头失败:', e)
    tipsHtml.value = '<div class="tip tip-err">启动失败: ' + e.message + '</div>'
    btnText.value = '开启摄像头'
    btnDisabled.value = false
  }
}

function stopCamera() {
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
    localStream = null
  }
  if (animId) {
    cancelAnimationFrame(animId)
    animId = null
  }
  videoRef.value.srcObject = null
  isRunning.value = false
  btnText.value = '开启摄像头'
  btnDisabled.value = false
}

function toggleCamera() {
  isRunning.value ? stopCamera() : startCamera()
}

function processFrame() {
  if (!localStream || !poseLandmarker) return
  animId = requestAnimationFrame(processFrame)

  if (videoRef.value.readyState < 2) return

  const now = performance.now()
  const videoCanvas = videoCanvasRef.value
  const videoCtx = videoCanvas.getContext('2d')
  const skelCanvas = skelCanvasRef.value
  const skelCtx = skelCanvas.getContext('2d')

  let results = null
  try {
    results = poseLandmarker.detectForVideo(videoRef.value, now)
  } catch (e) {
    console.warn('detectForVideo error:', e)
    return
  }

  videoCtx.save()
  videoCtx.translate(videoCanvas.width, 0)
  videoCtx.scale(-1, 1)
  videoCtx.drawImage(videoRef.value, 0, 0, videoCanvas.width, videoCanvas.height)
  videoCtx.restore()

  if (results && results.worldLandmarks && results.worldLandmarks.length > 0) {
    const world = results.worldLandmarks[0]
    const screen = results.landmarks[0]
    drawSkeleton2D(videoCtx, screen, videoCanvas.width, videoCanvas.height)
    drawSkeleton3D(world)
    updateTips(screen)
  }

  frameCount++
  if (now - lastFpsTime > 1000) {
    fpsText.value = 'FPS: ' + frameCount
    frameCount = 0
    lastFpsTime = now
  }
}

function drawSkeleton2D(ctx, landmarks, w, h) {
  const style = boneStyle.value
  ctx.save()
  ctx.translate(w, 0)
  ctx.scale(-1, 1)

  for (const [a, b] of CONNECTIONS) {
    if (landmarks[a].visibility < 0.3 || landmarks[b].visibility < 0.3) continue
    const ax = landmarks[a].x * w, ay = landmarks[a].y * h
    const bx = landmarks[b].x * w, by = landmarks[b].y * h

    ctx.beginPath()
    ctx.moveTo(ax, ay)
    ctx.lineTo(bx, by)

    if (style === 'neon') {
      ctx.strokeStyle = `hsl(${(a * 20) % 360}, 100%, 60%)`
      ctx.lineWidth = 4
      ctx.shadowColor = ctx.strokeStyle
      ctx.shadowBlur = 10
    } else if (style === 'xray') {
      ctx.strokeStyle = 'rgba(100, 200, 255, 0.8)'
      ctx.lineWidth = 2
    } else {
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 5
    }
    ctx.stroke()
    ctx.shadowBlur = 0
  }

  for (let i = 0; i < landmarks.length; i++) {
    if (landmarks[i].visibility < 0.3) continue
    const x = landmarks[i].x * w
    const y = landmarks[i].y * h
    ctx.beginPath()
    ctx.arc(x, y, style === 'cartoon' ? 6 : 3, 0, Math.PI * 2)
    ctx.fillStyle = style === 'neon' ? '#fff' : (style === 'xray' ? 'rgba(100,200,255,0.9)' : '#ff5722')
    ctx.fill()
  }

  ctx.restore()
}

function drawSkeleton3D(worldLandmarks) {
  const skelCanvas = skelCanvasRef.value
  const skelCtx = skelCanvas.getContext('2d')
  const W = skelCanvas.width
  const H = skelCanvas.height
  skelCtx.fillStyle = '#0a0a0a'
  skelCtx.fillRect(0, 0, W, H)

  const currentViewMode = viewMode.value
  const style = boneStyle.value

  if (autoRotate) rotY += 0.005

  function project(lm) {
    let x = lm.x, y = -lm.y, z = -lm.z

    if (currentViewMode === '3d') {
      const cosY = Math.cos(rotY), sinY = Math.sin(rotY)
      const nx = x * cosY - z * sinY
      const nz = x * sinY + z * cosY
      x = nx; z = nz

      const cosX = Math.cos(rotX), sinX = Math.sin(rotX)
      const ny = y * cosX - z * sinX
      const nz2 = y * sinX + z * cosX
      y = ny; z = nz2

      const fov = 3
      const scale = fov / (fov + z)
      return { x: W / 2 + x * scale * W * 0.4, y: H / 2 + y * scale * H * 0.4, z, scale }
    } else if (currentViewMode === 'side') {
      return { x: W / 2 + z * W * 0.4, y: H / 2 + y * H * 0.4, z: 0, scale: 1 }
    } else {
      return { x: W / 2 + x * W * 0.4, y: H / 2 + y * H * 0.4, z: 0, scale: 1 }
    }
  }

  const projected = worldLandmarks.map(lm => project(lm))

  skelCtx.strokeStyle = '#1a1a1a'
  skelCtx.lineWidth = 1
  for (let i = -5; i <= 5; i++) {
    const p1 = project({ x: i * 0.2, y: -1.5, z: 0 })
    const p2 = project({ x: i * 0.2, y: 1.5, z: 0 })
    skelCtx.beginPath(); skelCtx.moveTo(p1.x, p1.y); skelCtx.lineTo(p2.x, p2.y); skelCtx.stroke()
    const p3 = project({ x: -1, y: i * 0.3 - 0.5, z: 0 })
    const p4 = project({ x: 1, y: i * 0.3 - 0.5, z: 0 })
    skelCtx.beginPath(); skelCtx.moveTo(p3.x, p3.y); skelCtx.lineTo(p4.x, p4.y); skelCtx.stroke()
  }

  for (const [a, b] of CONNECTIONS) {
    const pa = projected[a], pb = projected[b]
    if (!pa || !pb) continue

    skelCtx.beginPath()
    skelCtx.moveTo(pa.x, pa.y)
    skelCtx.lineTo(pb.x, pb.y)

    if (style === 'neon') {
      const hue = (a * 25) % 360
      skelCtx.strokeStyle = `hsla(${hue}, 100%, 60%, ${0.5 + pa.scale * 0.3})`
      skelCtx.lineWidth = (pa.scale + pb.scale) * 2
      skelCtx.shadowColor = skelCtx.strokeStyle
      skelCtx.shadowBlur = 8
    } else if (style === 'xray') {
      skelCtx.strokeStyle = `rgba(100, 200, 255, ${0.4 + pa.scale * 0.3})`
      skelCtx.lineWidth = (pa.scale + pb.scale) * 1
    } else {
      skelCtx.strokeStyle = `rgba(255, 255, 255, ${0.5 + pa.scale * 0.3})`
      skelCtx.lineWidth = (pa.scale + pb.scale) * 2.5
    }
    skelCtx.stroke()
    skelCtx.shadowBlur = 0
  }

  for (let i = 0; i < projected.length; i++) {
    const p = projected[i]
    if (!p) continue
    const r = p.scale * (style === 'cartoon' ? 6 : 3)
    skelCtx.beginPath()
    skelCtx.arc(p.x, p.y, r, 0, Math.PI * 2)
    skelCtx.fillStyle = style === 'neon' ?
      `hsla(${(i * 25) % 360}, 100%, 70%, ${p.scale})` :
      (style === 'xray' ? `rgba(100,200,255,${p.scale})` : `rgba(255,87,34,${p.scale})`)
    skelCtx.fill()
  }
}

function updateTips(landmarks) {
  const tips = []
  const L = POSE_LANDMARKS

  const lShoulder = landmarks[L.LEFT_SHOULDER]
  const rShoulder = landmarks[L.RIGHT_SHOULDER]
  const shoulderDiff = Math.abs(lShoulder.y - rShoulder.y)
  if (shoulderDiff < 0.03) {
    tips.push({ text: '肩膀平衡 ✓', cls: 'tip-ok' })
  } else {
    tips.push({ text: '肩膀不平，请调整姿势', cls: 'tip-warn' })
  }

  const lHip = landmarks[L.LEFT_HIP]
  const rHip = landmarks[L.RIGHT_HIP]
  const midShoulder = { x: (lShoulder.x + rShoulder.x) / 2, y: (lShoulder.y + rShoulder.y) / 2 }
  const midHip = { x: (lHip.x + rHip.x) / 2, y: (lHip.y + rHip.y) / 2 }
  const backAngle = Math.abs(Math.atan2(midShoulder.x - midHip.x, midShoulder.y - midHip.y))
  if (backAngle < 0.15) {
    tips.push({ text: '背部挺直 ✓', cls: 'tip-ok' })
  } else {
    tips.push({ text: '注意背部姿势', cls: 'tip-warn' })
  }

  const nose = landmarks[L.NOSE]
  const headTilt = Math.abs(nose.x - midShoulder.x)
  if (headTilt < 0.05) {
    tips.push({ text: '头部位置正确 ✓', cls: 'tip-ok' })
  } else {
    tips.push({ text: '头部前倾，请抬头', cls: 'tip-warn' })
  }

  const lElbow = landmarks[L.LEFT_ELBOW]
  const lWrist = landmarks[L.LEFT_WRIST]
  const armAngle = Math.abs(Math.atan2(lWrist.y - lElbow.y, lWrist.x - lElbow.x))
  if (armAngle > 0.5 && armAngle < 2.5) {
    tips.push({ text: '手臂角度良好 ✓', cls: 'tip-ok' })
  } else {
    tips.push({ text: '调整手臂角度', cls: 'tip-err' })
  }

  tipsHtml.value = tips.map(t => `<div class="tip ${t.cls}">${t.text}</div>`).join('')
}

function takePhoto() {
  const link = document.createElement('a')
  link.download = 'pose_' + Date.now() + '.png'
  const combo = document.createElement('canvas')
  combo.width = videoCanvasRef.value.width + skelCanvasRef.value.width
  combo.height = Math.max(videoCanvasRef.value.height, skelCanvasRef.value.height)
  const c = combo.getContext('2d')
  c.drawImage(videoCanvasRef.value, 0, 0)
  c.drawImage(skelCanvasRef.value, videoCanvasRef.value.width, 0)
  link.href = combo.toDataURL()
  link.click()
}

function onSkelMouseDown(e) {
  isDragging = true
  autoRotate = false
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onSkelMouseMove(e) {
  if (!isDragging) return
  rotY += (e.clientX - lastMouse.x) * 0.01
  rotX += (e.clientY - lastMouse.y) * 0.01
  lastMouse = { x: e.clientX, y: e.clientY }
}

function onSkelMouseUp() {
  isDragging = false
}

function onSkelDblClick() {
  autoRotate = true
}

function onCameraChange(deviceId) {
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

  const skelCanvas = skelCanvasRef.value
  skelCanvas.addEventListener('mousedown', onSkelMouseDown)
  skelCanvas.addEventListener('mousemove', onSkelMouseMove)
  skelCanvas.addEventListener('mouseup', onSkelMouseUp)
  skelCanvas.addEventListener('dblclick', onSkelDblClick)
})

onUnmounted(() => {
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
    localStream = null
  }
  if (animId) {
    cancelAnimationFrame(animId)
    animId = null
  }
  if (videoRef.value) {
    videoRef.value.srcObject = null
  }
  const skelCanvas = skelCanvasRef.value
  if (skelCanvas) {
    skelCanvas.removeEventListener('mousedown', onSkelMouseDown)
    skelCanvas.removeEventListener('mousemove', onSkelMouseMove)
    skelCanvas.removeEventListener('mouseup', onSkelMouseUp)
    skelCanvas.removeEventListener('dblclick', onSkelDblClick)
  }
})
</script>

<style scoped>
.pose-skeleton {
  font-family: -apple-system, sans-serif;
  background: #0a0a0a;
  color: #e0e0e0;
  min-height: 100vh;
  display: flex;
}

.sidebar {
  width: 280px;
  background: #111;
  border-right: 1px solid #222;
  padding: 16px;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar h2 {
  font-size: 16px;
}

.sidebar a {
  color: #667eea;
  text-decoration: none;
  font-size: 13px;
}

.main {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 12px;
}

.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #111;
  border-radius: 12px;
  overflow: hidden;
}

.panel-header {
  padding: 10px 16px;
  width: 100%;
  text-align: center;
  font-size: 13px;
  color: #888;
  border-bottom: 1px solid #222;
}

.panel-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  position: relative;
}

canvas {
  max-width: 100%;
  max-height: 100%;
  border-radius: 0 0 12px 12px;
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

.tips-panel {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.8;
  max-height: 200px;
  overflow-y: auto;
}

.tips-panel :deep(.tip) {
  padding: 4px 0;
  border-bottom: 1px solid #222;
}

.tips-panel :deep(.tip:last-child) {
  border: none;
}

.tips-panel :deep(.tip-ok) {
  color: #4caf50;
}

.tips-panel :deep(.tip-warn) {
  color: #ff9800;
}

.tips-panel :deep(.tip-err) {
  color: #f44336;
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

select {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e0e0e0;
  padding: 6px;
  font-size: 13px;
}
</style>