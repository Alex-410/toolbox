<template>
  <div class="page">
    <div class="sidebar">
      <router-link to="/camera">&larr; 返回工具集</router-link>
      <h2>3D 人脸贴纸相机</h2>

      <div class="setting-group">
        <label>选择贴纸</label>
        <div class="sticker-grid">
          <div
            v-for="s in stickers"
            :key="s.id"
            :class="['sticker-btn', { active: currentSticker === s.id }]"
            @click="currentSticker = s.id"
          >
            <span class="icon">{{ s.icon }}</span>{{ s.label }}
          </div>
        </div>
      </div>

      <div class="setting-group">
        <label>贴纸大小: {{ stickerScale.toFixed(1) }}</label>
        <input type="range" min="50" max="200" :value="stickerScale * 100" @input="stickerScale = +$event.target.value / 100" />
      </div>

      <div class="setting-group">
        <label>贴纸颜色</label>
        <div style="display:flex; gap:4px; flex-wrap:wrap;">
          <div
            v-for="c in colorOptions"
            :key="c"
            class="color-btn"
            :data-color="c"
            :style="{ width: '24px', height: '24px', background: c, borderRadius: '50%', cursor: 'pointer', border: '2px solid ' + (stickerColor === c ? '#667eea' : 'transparent') }"
            @click="stickerColor = c"
          ></div>
        </div>
      </div>

      <div ref="cameraSelectorContainer"></div>

      <div class="controls">
        <button :class="{ primary: !stream }" @click="toggleCamera">{{ stream ? '关闭摄像头' : '开启摄像头' }}</button>
        <button @click="takePhoto">拍照</button>
        <button :class="{ active: isRecording }" @click="toggleRecord">{{ isRecording ? '停止录像' : '录像' }}</button>
      </div>

      <div style="font-size:11px; color:#555;">FPS: {{ fps }}</div>
    </div>

    <div class="main">
      <div class="status-bar">{{ statusBar }}</div>
      <div class="video-container">
        <video ref="videoRef" autoplay playsinline></video>
        <canvas ref="canvasRef"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { FaceLandmarker, FilesetResolver } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs'
import { useCamera } from '../../composables/useCamera.js'

const { initCameraSelector, getSelectedStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const cameraSelectorContainer = ref(null)

const stickers = [
  { id: 'sunglasses', icon: '🕶️', label: '墨镜' },
  { id: 'hat', icon: '🎩', label: '礼帽' },
  { id: 'crown', icon: '👑', label: '皇冠' },
  { id: 'mask', icon: '😷', label: '口罩' },
  { id: 'heart_eyes', icon: '😍', label: '爱心眼' },
  { id: 'dog', icon: '🐶', label: '狗耳朵' },
  { id: 'cat', icon: '🐱', label: '猫耳朵' },
  { id: 'devil', icon: '😈', label: '恶魔角' },
  { id: 'star', icon: '⭐', label: '星星眼' },
  { id: 'glasses3d', icon: '🤓', label: '3D眼镜' }
]

const colorOptions = ['#000', '#ff0000', '#00ff00', '#0000ff', '#ff00ff', '#ffff00', '#ffffff']

const statusBar = ref('等待开启摄像头')
const fps = ref('--')
const currentSticker = ref('sunglasses')
const stickerScale = ref(1.0)
const stickerColor = ref('#000')
const isRecording = ref(false)

let faceLandmarker = null
let stream = null
let animId = null
let mediaRecorder = null
let recordedChunks = []
let frameCount = 0
let lastFpsTime = performance.now()

let ctx = null

const MODEL_PATHS = [
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
  './models/face_landmarker.task',
  './models/face_landmarker.tflite'
]

function toggleCamera() {
  if (stream) {
    stopCamera()
  } else {
    startCamera()
  }
}

async function onCameraSwitch(deviceId) {
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = await getSelectedStream()
    videoRef.value.srcObject = stream
  }
}

async function initModel() {
  statusBar.value = '加载人脸关键点模型...'
  try {
    const vision = await FilesetResolver.forVisionTasks(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
    )

    let modelLoaded = false
    for (const modelPath of MODEL_PATHS) {
      try {
        statusBar.value = `尝试加载模型: ${modelPath.includes('http') ? '远程' : '本地'}...`
        faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: modelPath,
            delegate: 'GPU'
          },
          runningMode: 'VIDEO',
          numFaces: 1,
          outputFaceBlendshapes: false
        })
        console.log('模型加载成功:', modelPath)
        modelLoaded = true
        break
      } catch (e) {
        console.warn('模型加载失败:', modelPath, e.message)
        continue
      }
    }

    if (!modelLoaded) {
      throw new Error('All model sources failed. Run download_model.ps1 to get the model locally, or enable proxy.')
    }

    statusBar.value = '模型加载完成'
    return true
  } catch (e) {
    console.error(e)
    statusBar.value = '模型加载失败: ' + e.message
    return false
  }
}

async function startCamera() {
  try {
    stream = await getSelectedStream()
    videoRef.value.srcObject = stream
    await videoRef.value.play()

    canvasRef.value.width = videoRef.value.videoWidth
    canvasRef.value.height = videoRef.value.videoHeight

    if (!faceLandmarker) {
      const ok = await initModel()
      if (!ok) return
    }

    statusBar.value = '运行中 - 检测人脸'
    processFrame()
  } catch (e) {
    statusBar.value = '摄像头错误: ' + e.message
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  if (animId) {
    cancelAnimationFrame(animId)
    animId = null
  }
  videoRef.value.srcObject = null
  statusBar.value = '已停止'
}

function processFrame() {
  if (!stream || !faceLandmarker) return
  animId = requestAnimationFrame(processFrame)

  if (videoRef.value.readyState < 2) return

  const now = performance.now()

  let results = null
  try {
    results = faceLandmarker.detectForVideo(videoRef.value, now)
  } catch (e) {
    console.warn('detectForVideo error:', e)
    return
  }

  ctx.save()
  ctx.translate(canvasRef.value.width, 0)
  ctx.scale(-1, 1)
  ctx.drawImage(videoRef.value, 0, 0, canvasRef.value.width, canvasRef.value.height)
  ctx.restore()

  if (results && results.faceLandmarks && results.faceLandmarks.length > 0) {
    for (const landmarks of results.faceLandmarks) {
      drawSticker(landmarks)
    }
  }

  frameCount++
  if (now - lastFpsTime > 1000) {
    fps.value = frameCount
    frameCount = 0
    lastFpsTime = now
  }
}

function getPoint(landmarks, idx) {
  return { x: (1 - landmarks[idx].x) * canvasRef.value.width, y: landmarks[idx].y * canvasRef.value.height }
}

function dist(a, b) { return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2) }

function drawSticker(landmarks) {
  const leftEye = getPoint(landmarks, 33)
  const rightEye = getPoint(landmarks, 263)
  const nose = getPoint(landmarks, 1)
  const chin = getPoint(landmarks, 152)
  const forehead = getPoint(landmarks, 10)
  const leftEar = getPoint(landmarks, 234)
  const rightEar = getPoint(landmarks, 454)
  const leftMouth = getPoint(landmarks, 61)
  const rightMouth = getPoint(landmarks, 291)
  const upperLip = getPoint(landmarks, 13)
  const lowerLip = getPoint(landmarks, 14)

  const eyeDist = dist(leftEye, rightEye)
  const faceWidth = dist(leftEar, rightEar)
  const faceAngle = Math.atan2(rightEye.y - leftEye.y, rightEye.x - leftEye.x)
  const s = stickerScale.value

  ctx.save()

  switch (currentSticker.value) {
    case 'sunglasses': drawSunglasses(leftEye, rightEye, eyeDist, faceAngle, s); break
    case 'hat': drawHat(forehead, leftEar, rightEar, faceWidth, faceAngle, s); break
    case 'crown': drawCrown(forehead, leftEar, rightEar, faceWidth, faceAngle, s); break
    case 'mask': drawMask(nose, leftMouth, rightMouth, lowerLip, chin, faceWidth, faceAngle, s); break
    case 'heart_eyes': drawHeartEyes(leftEye, rightEye, eyeDist, faceAngle, s); break
    case 'dog': drawDogEars(forehead, leftEar, rightEar, faceWidth, faceAngle, s); break
    case 'cat': drawCatEars(forehead, leftEar, rightEar, faceWidth, faceAngle, s); break
    case 'devil': drawDevilHorns(forehead, leftEar, rightEar, faceWidth, faceAngle, s); break
    case 'star': drawStarEyes(leftEye, rightEye, eyeDist, faceAngle, s); break
    case 'glasses3d': draw3DGlasses(leftEye, rightEye, eyeDist, faceAngle, s); break
  }

  ctx.restore()
}

function drawSunglasses(leftEye, rightEye, eyeDist, angle, s) {
  const cx = (leftEye.x + rightEye.x) / 2
  const cy = (leftEye.y + rightEye.y) / 2
  const w = eyeDist * 2.2 * s
  const h = eyeDist * 0.7 * s

  ctx.save()
  ctx.translate(cx, cy)
  ctx.rotate(angle)

  ctx.strokeStyle = stickerColor.value
  ctx.lineWidth = 3 * s
  ctx.fillStyle = 'rgba(0,0,0,0.75)'

  ctx.beginPath()
  ctx.ellipse(-eyeDist * 0.5, 0, w * 0.28, h * 0.45, 0, 0, Math.PI * 2)
  ctx.fill(); ctx.stroke()

  ctx.beginPath()
  ctx.ellipse(eyeDist * 0.5, 0, w * 0.28, h * 0.45, 0, 0, Math.PI * 2)
  ctx.fill(); ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(-eyeDist * 0.22, 0)
  ctx.lineTo(eyeDist * 0.22, 0)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(-eyeDist * 0.78, -h * 0.1)
  ctx.lineTo(-eyeDist * 1.2, -h * 0.3)
  ctx.moveTo(eyeDist * 0.78, -h * 0.1)
  ctx.lineTo(eyeDist * 1.2, -h * 0.3)
  ctx.stroke()

  ctx.fillStyle = 'rgba(255,255,255,0.15)'
  ctx.beginPath()
  ctx.ellipse(-eyeDist * 0.55, -h * 0.15, w * 0.1, h * 0.15, -0.3, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.ellipse(eyeDist * 0.45, -h * 0.15, w * 0.1, h * 0.15, -0.3, 0, Math.PI * 2)
  ctx.fill()

  ctx.restore()
}

function drawHat(forehead, leftEar, rightEar, faceWidth, angle, s) {
  const cx = (leftEar.x + rightEar.x) / 2
  const w = faceWidth * 1.1 * s
  ctx.save()
  ctx.translate(cx, forehead.y - faceWidth * 0.15)
  ctx.rotate(angle)

  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.ellipse(0, 0, w * 0.6, w * 0.08, 0, 0, Math.PI * 2)
  ctx.fill()

  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.moveTo(-w * 0.3, 0)
  ctx.lineTo(-w * 0.25, -w * 0.45)
  ctx.lineTo(w * 0.25, -w * 0.45)
  ctx.lineTo(w * 0.3, 0)
  ctx.closePath()
  ctx.fill()

  ctx.fillStyle = '#c62828'
  ctx.fillRect(-w * 0.3, -w * 0.08, w * 0.6, w * 0.08)

  ctx.restore()
}

function drawCrown(forehead, leftEar, rightEar, faceWidth, angle, s) {
  const cx = (leftEar.x + rightEar.x) / 2
  const w = faceWidth * 0.9 * s
  ctx.save()
  ctx.translate(cx, forehead.y - faceWidth * 0.1)
  ctx.rotate(angle)

  ctx.fillStyle = '#ffd700'
  ctx.strokeStyle = '#b8860b'
  ctx.lineWidth = 2

  ctx.beginPath()
  ctx.moveTo(-w * 0.4, 0)
  ctx.lineTo(-w * 0.4, -w * 0.2)
  ctx.lineTo(-w * 0.2, -w * 0.1)
  ctx.lineTo(0, -w * 0.35)
  ctx.lineTo(w * 0.2, -w * 0.1)
  ctx.lineTo(w * 0.4, -w * 0.2)
  ctx.lineTo(w * 0.4, 0)
  ctx.closePath()
  ctx.fill(); ctx.stroke()

  ctx.fillStyle = '#e53935'
  ctx.beginPath(); ctx.arc(0, -w * 0.15, w * 0.04, 0, Math.PI * 2); ctx.fill()
  ctx.fillStyle = '#1e88e5'
  ctx.beginPath(); ctx.arc(-w * 0.25, -w * 0.05, w * 0.03, 0, Math.PI * 2); ctx.fill()
  ctx.beginPath(); ctx.arc(w * 0.25, -w * 0.05, w * 0.03, 0, Math.PI * 2); ctx.fill()

  ctx.restore()
}

function drawMask(nose, leftMouth, rightMouth, lowerLip, chin, faceWidth, angle, s) {
  const cx = nose.x
  const cy = (nose.y + lowerLip.y) / 2
  const w = faceWidth * 0.85 * s
  const h = dist(nose, chin) * 0.9 * s

  ctx.save()
  ctx.translate(cx, cy)
  ctx.rotate(angle)

  ctx.fillStyle = 'rgba(255,255,255,0.9)'
  ctx.beginPath()
  ctx.moveTo(-w * 0.5, -h * 0.3)
  ctx.quadraticCurveTo(-w * 0.55, h * 0.3, 0, h * 0.5)
  ctx.quadraticCurveTo(w * 0.55, h * 0.3, w * 0.5, -h * 0.3)
  ctx.closePath()
  ctx.fill()

  ctx.strokeStyle = '#ccc'
  ctx.lineWidth = 1.5
  ctx.stroke()

  ctx.strokeStyle = '#aaa'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(-w * 0.5, -h * 0.2)
  ctx.quadraticCurveTo(-w * 0.7, 0, -w * 0.5, h * 0.2)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(w * 0.5, -h * 0.2)
  ctx.quadraticCurveTo(w * 0.7, 0, w * 0.5, h * 0.2)
  ctx.stroke()

  ctx.restore()
}

function drawHeartEyes(leftEye, rightEye, eyeDist, angle, s) {
  const size = eyeDist * 0.35 * s
  drawHeart(leftEye.x, leftEye.y, size, '#e91e63')
  drawHeart(rightEye.x, rightEye.y, size, '#e91e63')
}

function drawHeart(x, y, size, color) {
  ctx.save()
  ctx.translate(x, y)
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.moveTo(0, size * 0.3)
  ctx.bezierCurveTo(-size, -size * 0.3, -size * 0.5, -size, 0, -size * 0.4)
  ctx.bezierCurveTo(size * 0.5, -size, size, -size * 0.3, 0, size * 0.3)
  ctx.fill()
  ctx.restore()
}

function drawDogEars(forehead, leftEar, rightEar, faceWidth, angle, s) {
  const w = faceWidth * 0.35 * s
  ctx.save()
  ctx.translate(leftEar.x, leftEar.y - faceWidth * 0.3)
  ctx.rotate(angle - 0.3)
  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.ellipse(0, 0, w * 0.4, w, -0.2, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#ffcccc'
  ctx.beginPath()
  ctx.ellipse(0, 0, w * 0.2, w * 0.6, -0.2, 0, Math.PI * 2)
  ctx.fill()
  ctx.restore()

  ctx.save()
  ctx.translate(rightEar.x, rightEar.y - faceWidth * 0.3)
  ctx.rotate(angle + 0.3)
  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.ellipse(0, 0, w * 0.4, w, 0.2, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#ffcccc'
  ctx.beginPath()
  ctx.ellipse(0, 0, w * 0.2, w * 0.6, 0.2, 0, Math.PI * 2)
  ctx.fill()
  ctx.restore()
}

function drawCatEars(forehead, leftEar, rightEar, faceWidth, angle, s) {
  const w = faceWidth * 0.3 * s
  ctx.save()
  ctx.translate(leftEar.x, leftEar.y - faceWidth * 0.25)
  ctx.rotate(angle - 0.2)
  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.moveTo(0, w)
  ctx.lineTo(-w * 0.6, -w * 0.8)
  ctx.lineTo(w * 0.6, -w * 0.8)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#ffcccc'
  ctx.beginPath()
  ctx.moveTo(0, w * 0.5)
  ctx.lineTo(-w * 0.3, -w * 0.4)
  ctx.lineTo(w * 0.3, -w * 0.4)
  ctx.closePath()
  ctx.fill()
  ctx.restore()

  ctx.save()
  ctx.translate(rightEar.x, rightEar.y - faceWidth * 0.25)
  ctx.rotate(angle + 0.2)
  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.moveTo(0, w)
  ctx.lineTo(-w * 0.6, -w * 0.8)
  ctx.lineTo(w * 0.6, -w * 0.8)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#ffcccc'
  ctx.beginPath()
  ctx.moveTo(0, w * 0.5)
  ctx.lineTo(-w * 0.3, -w * 0.4)
  ctx.lineTo(w * 0.3, -w * 0.4)
  ctx.closePath()
  ctx.fill()
  ctx.restore()
}

function drawDevilHorns(forehead, leftEar, rightEar, faceWidth, angle, s) {
  const w = faceWidth * 0.2 * s
  ctx.save()
  ctx.translate(leftEar.x, leftEar.y - faceWidth * 0.35)
  ctx.rotate(angle - 0.15)
  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.moveTo(-w * 0.5, w)
  ctx.lineTo(0, -w * 2)
  ctx.lineTo(w * 0.5, w)
  ctx.closePath()
  ctx.fill()
  ctx.restore()

  ctx.save()
  ctx.translate(rightEar.x, rightEar.y - faceWidth * 0.35)
  ctx.rotate(angle + 0.15)
  ctx.fillStyle = stickerColor.value
  ctx.beginPath()
  ctx.moveTo(-w * 0.5, w)
  ctx.lineTo(0, -w * 2)
  ctx.lineTo(w * 0.5, w)
  ctx.closePath()
  ctx.fill()
  ctx.restore()
}

function drawStarEyes(leftEye, rightEye, eyeDist, angle, s) {
  const size = eyeDist * 0.3 * s
  drawStar(leftEye.x, leftEye.y, size, '#ffeb3b')
  drawStar(rightEye.x, rightEye.y, size, '#ffeb3b')
}

function drawStar(x, y, size, color) {
  ctx.save()
  ctx.translate(x, y)
  ctx.fillStyle = color
  ctx.beginPath()
  for (let i = 0; i < 5; i++) {
    const a = (i * 4 * Math.PI / 5) - Math.PI / 2
    const r = i === 0 ? size : size
    ctx.lineTo(Math.cos(a) * size, Math.sin(a) * size)
    const b = a + 2 * Math.PI / 5
    ctx.lineTo(Math.cos(b) * size * 0.4, Math.sin(b) * size * 0.4)
  }
  ctx.closePath()
  ctx.fill()
  ctx.restore()
}

function draw3DGlasses(leftEye, rightEye, eyeDist, angle, s) {
  const cx = (leftEye.x + rightEye.x) / 2
  const cy = (leftEye.y + rightEye.y) / 2
  const w = eyeDist * 2.2 * s
  const h = eyeDist * 0.7 * s

  ctx.save()
  ctx.translate(cx, cy)
  ctx.rotate(angle)

  ctx.fillStyle = 'rgba(255,0,0,0.5)'
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 3 * s
  ctx.beginPath()
  ctx.ellipse(-eyeDist * 0.5, 0, w * 0.28, h * 0.45, 0, 0, Math.PI * 2)
  ctx.fill(); ctx.stroke()

  ctx.fillStyle = 'rgba(0,255,255,0.5)'
  ctx.beginPath()
  ctx.ellipse(eyeDist * 0.5, 0, w * 0.28, h * 0.45, 0, 0, Math.PI * 2)
  ctx.fill(); ctx.stroke()

  ctx.strokeStyle = '#333'
  ctx.beginPath()
  ctx.moveTo(-eyeDist * 0.22, 0)
  ctx.lineTo(eyeDist * 0.22, 0)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(-eyeDist * 0.78, -h * 0.1)
  ctx.lineTo(-eyeDist * 1.2, -h * 0.3)
  ctx.moveTo(eyeDist * 0.78, -h * 0.1)
  ctx.lineTo(eyeDist * 1.2, -h * 0.3)
  ctx.stroke()

  ctx.restore()
}

function takePhoto() {
  const link = document.createElement('a')
  link.download = 'face_sticker_' + Date.now() + '.png'
  link.href = canvasRef.value.toDataURL()
  link.click()
}

function toggleRecord() {
  if (!isRecording.value) {
    recordedChunks = []
    mediaRecorder = new MediaRecorder(canvasRef.value.captureStream(30), { mimeType: 'video/webm' })
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data) }
    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'video/webm' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'face_sticker_' + Date.now() + '.webm'; a.click()
      URL.revokeObjectURL(url)
    }
    mediaRecorder.start(100)
    isRecording.value = true
  } else {
    mediaRecorder.stop()
    isRecording.value = false
  }
}

onMounted(async () => {
  ctx = canvasRef.value.getContext('2d')
  await nextTick()
  initCameraSelector(cameraSelectorContainer.value, onCameraSwitch)
})

onUnmounted(() => {
  if (animId) {
    cancelAnimationFrame(animId)
    animId = null
  }
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  if (faceLandmarker) {
    faceLandmarker.close()
    faceLandmarker = null
  }
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
})
</script>

<style scoped>
* { margin: 0; padding: 0; box-sizing: border-box; }

.page {
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

.sidebar h2 { font-size: 16px; }
.sidebar a { color: #667eea; text-decoration: none; font-size: 13px; }

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  position: relative;
}

.video-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0,0,0,0.5);
}

video { display: none; }

canvas {
  display: block;
  border-radius: 12px;
  max-width: 100%;
  max-height: 75vh;
}

.sticker-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.sticker-btn {
  padding: 10px 8px;
  background: #1a1a1a;
  border: 2px solid #2a2a2a;
  border-radius: 10px;
  cursor: pointer;
  text-align: center;
  font-size: 12px;
  color: #aaa;
  transition: all 0.15s;
}

.sticker-btn:hover { border-color: #444; background: #222; }
.sticker-btn.active { border-color: #667eea; background: #1a1a3a; color: #fff; }
.sticker-btn .icon { font-size: 28px; display: block; margin-bottom: 4px; }

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
button.active { background: #c62828; border-color: #c62828; }

.controls {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.status-bar {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.7);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  color: #aaa;
  z-index: 5;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

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
</style>
