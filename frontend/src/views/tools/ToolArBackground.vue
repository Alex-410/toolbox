<template>
  <div class="page">
    <div class="sidebar">
      <router-link to="/camera">&larr; 返回工具集</router-link>
      <h2>AR 背景替换</h2>

      <div class="setting-group">
        <label>背景模式</label>
        <div class="bg-grid">
          <div
            v-for="bg in bgOptions"
            :key="bg.id"
            :class="['bg-option', { active: bgMode === bg.id }]"
            :style="bg.style"
            @click="selectBg(bg.id)"
          >{{ bg.label }}</div>
        </div>
      </div>

      <div ref="cameraSelectorContainer"></div>

      <input ref="bgFileInput" type="file" accept="image/*" style="display:none;" @change="onBgFileChange" />

      <div class="setting-group">
        <label>边缘柔化: {{ edgeSmooth }}px</label>
        <input type="range" min="0" max="20" :value="edgeSmooth" @input="edgeSmooth = +$event.target.value" />
      </div>

      <div class="setting-group">
        <label>分割阈值: {{ threshold.toFixed(2) }}</label>
        <input type="range" min="0" max="100" :value="threshold * 100" @input="threshold = +$event.target.value / 100" />
      </div>

      <div class="setting-group">
        <label>背景模糊强度: {{ bgBlur }}</label>
        <input type="range" min="0" max="40" :value="bgBlur" @input="bgBlur = +$event.target.value" />
      </div>

      <div class="controls">
        <button :class="{ primary: !stream }" @click="toggleCamera">{{ stream ? '关闭摄像头' : '开启摄像头' }}</button>
        <button @click="takePhoto">拍照</button>
        <button :class="{ active: isRecording }" @click="toggleRecord">{{ isRecording ? '停止录像' : '录像' }}</button>
      </div>

      <div style="font-size:11px; color:#555;">FPS: {{ fps }}</div>
    </div>

    <div class="main">
      <div class="status-bar">{{ statusBar }}</div>
      <div v-show="isLoading" class="loading-overlay">
        <div class="spinner"></div>
        <div style="font-size:13px; color:#aaa;">加载人像分割模型...</div>
      </div>
      <div class="video-container">
        <video ref="videoRef" autoplay playsinline></video>
        <canvas ref="canvasRef"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ImageSegmenter, FilesetResolver } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs'
import { useCamera } from '../../composables/useCamera.js'

const { initCameraSelector, getSelectedStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const cameraSelectorContainer = ref(null)
const bgFileInput = ref(null)

const bgOptions = [
  { id: 'blur', label: '模糊', style: { background: 'linear-gradient(135deg, #1a1a2e, #16213e)' } },
  { id: 'gradient1', label: '渐变1', style: { background: 'linear-gradient(135deg, #667eea, #764ba2)' } },
  { id: 'gradient2', label: '渐变2', style: { background: 'linear-gradient(135deg, #f093fb, #f5576c)' } },
  { id: 'gradient3', label: '渐变3', style: { background: 'linear-gradient(135deg, #4facfe, #00f2fe)' } },
  { id: 'green', label: '绿幕', style: { background: '#00b140' } },
  { id: 'black', label: '纯黑', style: { background: '#000' } },
  { id: 'image', label: '自定义图片', style: { background: '#222', borderStyle: 'dashed' } },
  { id: 'none', label: '原画', style: { background: '#1a1a1a' } }
]

const statusBar = ref('等待开启摄像头')
const isLoading = ref(false)
const fps = ref('--')
const bgMode = ref('blur')
const edgeSmooth = ref(5)
const threshold = ref(0.6)
const bgBlur = ref(15)
const isRecording = ref(false)

let segmenter = null
let stream = null
let customBgImg = null
let animId = null
let mediaRecorder = null
let recordedChunks = []
let frameCount = 0
let lastFpsTime = performance.now()

let ctx = null
const bgCanvas = document.createElement('canvas')
const bgCtx = bgCanvas.getContext('2d')
const tempCanvas = document.createElement('canvas')
const tempCtx = tempCanvas.getContext('2d')

function selectBg(id) {
  bgMode.value = id
  if (id === 'image') {
    bgFileInput.value.click()
  }
}

function onBgFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const img = new Image()
  img.onload = () => { customBgImg = img }
  img.src = URL.createObjectURL(file)
}

async function onCameraSwitch(deviceId) {
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = await getSelectedStream()
    videoRef.value.srcObject = stream
  }
}

function toggleCamera() {
  if (stream) {
    stopCamera()
  } else {
    startCamera()
  }
}

async function initSegmenter() {
  isLoading.value = true
  try {
    const vision = await FilesetResolver.forVisionTasks(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
    )
    segmenter = await ImageSegmenter.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite',
        delegate: 'GPU'
      },
      runningMode: 'VIDEO',
      outputCategoryMask: true
    })
    isLoading.value = false
    statusBar.value = '模型加载完成，开始处理'
    return true
  } catch (e) {
    console.error(e)
    isLoading.value = false
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
    bgCanvas.width = canvasRef.value.width
    bgCanvas.height = canvasRef.value.height
    tempCanvas.width = canvasRef.value.width
    tempCanvas.height = canvasRef.value.height

    if (!segmenter) {
      const ok = await initSegmenter()
      if (!ok) return
    }

    statusBar.value = '运行中'
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
  animId = requestAnimationFrame(processFrame)

  if (!stream || !segmenter) return
  if (videoRef.value.readyState < 2) return

  const now = performance.now()

  let result = null
  try {
    result = segmenter.segmentForVideo(videoRef.value, now)
  } catch (e) {
    return
  }

  if (result && result.categoryMask) {
    const mask = result.categoryMask.getAsUint8Array()
    renderFrame(mask)
    result.categoryMask.close()
  }

  frameCount++
  if (now - lastFpsTime > 1000) {
    fps.value = frameCount
    frameCount = 0
    lastFpsTime = now
  }
}

function renderFrame(mask) {
  const w = canvasRef.value.width
  const h = canvasRef.value.height

  drawBackground(w, h)
  const smoothMask = createSmoothMask(mask, w, h)

  ctx.drawImage(bgCanvas, 0, 0)

  tempCtx.drawImage(videoRef.value, 0, 0, w, h)

  const imageData = tempCtx.getImageData(0, 0, w, h)
  const bgData = bgCtx.getImageData(0, 0, w, h)
  const outData = ctx.getImageData(0, 0, w, h)

  for (let i = 0; i < smoothMask.length; i++) {
    const a = smoothMask[i]
    if (a > 0.01) {
      const idx = i * 4
      const inv = 1 - a
      outData.data[idx]     = imageData.data[idx]     * a + bgData.data[idx]     * inv
      outData.data[idx + 1] = imageData.data[idx + 1] * a + bgData.data[idx + 1] * inv
      outData.data[idx + 2] = imageData.data[idx + 2] * a + bgData.data[idx + 2] * inv
      outData.data[idx + 3] = 255
    }
  }

  ctx.putImageData(outData, 0, 0)
}

function createSmoothMask(mask, w, h) {
  const smooth = new Float32Array(w * h)
  for (let i = 0; i < mask.length; i++) {
    let val = mask[i] === 0 ? 1.0 : 0.0
    if (val > 0) {
      val = val > threshold.value ? 1.0 : val / threshold.value
    }
    smooth[i] = val
  }

  if (edgeSmooth.value > 0) {
    const kernel = Math.ceil(edgeSmooth.value)
    const temp = new Float32Array(smooth)
    for (let y = kernel; y < h - kernel; y++) {
      for (let x = kernel; x < w - kernel; x++) {
        const idx = y * w + x
        if (smooth[idx] > 0.01 && smooth[idx] < 0.99) {
          let sum = 0, count = 0
          for (let dy = -kernel; dy <= kernel; dy++) {
            for (let dx = -kernel; dx <= kernel; dx++) {
              sum += smooth[(y + dy) * w + (x + dx)]
              count++
            }
          }
          temp[idx] = sum / count
        }
      }
    }
    return temp
  }
  return smooth
}

function drawBackground(w, h) {
  bgCtx.clearRect(0, 0, w, h)

  switch (bgMode.value) {
    case 'blur':
      bgCtx.filter = `blur(${bgBlur.value}px)`
      bgCtx.drawImage(videoRef.value, 0, 0, w, h)
      bgCtx.filter = 'none'
      break
    case 'gradient1': {
      const g1 = bgCtx.createLinearGradient(0, 0, w, h)
      g1.addColorStop(0, '#667eea'); g1.addColorStop(1, '#764ba2')
      bgCtx.fillStyle = g1; bgCtx.fillRect(0, 0, w, h)
      break
    }
    case 'gradient2': {
      const g2 = bgCtx.createLinearGradient(0, 0, w, h)
      g2.addColorStop(0, '#f093fb'); g2.addColorStop(1, '#f5576c')
      bgCtx.fillStyle = g2; bgCtx.fillRect(0, 0, w, h)
      break
    }
    case 'gradient3': {
      const g3 = bgCtx.createLinearGradient(0, 0, w, h)
      g3.addColorStop(0, '#4facfe'); g3.addColorStop(1, '#00f2fe')
      bgCtx.fillStyle = g3; bgCtx.fillRect(0, 0, w, h)
      break
    }
    case 'green':
      bgCtx.fillStyle = '#00b140'; bgCtx.fillRect(0, 0, w, h)
      break
    case 'black':
      bgCtx.fillStyle = '#000'; bgCtx.fillRect(0, 0, w, h)
      break
    case 'image':
      if (customBgImg) {
        bgCtx.drawImage(customBgImg, 0, 0, w, h)
      } else {
        bgCtx.fillStyle = '#222'; bgCtx.fillRect(0, 0, w, h)
      }
      break
    case 'none':
      bgCtx.drawImage(videoRef.value, 0, 0, w, h)
      break
  }
}

function takePhoto() {
  const link = document.createElement('a')
  link.download = 'ar_photo_' + Date.now() + '.png'
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
      a.href = url; a.download = 'ar_video_' + Date.now() + '.webm'; a.click()
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
  if (segmenter) {
    segmenter.close()
    segmenter = null
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
  width: 300px;
  background: #111;
  border-right: 1px solid #222;
  padding: 20px;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar h2 { font-size: 18px; color: #fff; }
.sidebar a { color: #667eea; text-decoration: none; font-size: 13px; }

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
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

.controls {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

button {
  padding: 8px 16px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

button:hover { background: #2a2a2a; border-color: #555; }
button.primary { background: #1a73e8; border-color: #1a73e8; }
button.active { background: #667eea; border-color: #667eea; }

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting-group label { font-size: 12px; color: #888; }

.setting-group select,
.setting-group input[type="range"] {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e0e0e0;
  padding: 6px;
  font-size: 13px;
}

input[type="range"] {
  -webkit-appearance: none;
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

.bg-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.bg-option {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #aaa;
  text-align: center;
  padding: 4px;
}

.bg-option:hover { border-color: #555; }
.bg-option.active { border-color: #667eea; }

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
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  z-index: 10;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #333;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
