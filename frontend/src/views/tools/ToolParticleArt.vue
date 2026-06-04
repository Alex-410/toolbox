<template>
  <div class="particle-art">
    <div class="sidebar">
      <router-link to="/camera">&larr; 返回工具集</router-link>
      <h2>手势粒子交互</h2>

      <div class="setting-group">
        <label>交互模式</label>
        <div class="mode-grid">
          <div
            v-for="mode in modes"
            :key="mode.id"
            class="mode-btn"
            :class="{ active: interactionMode === mode.id }"
            @click="setMode(mode.id)"
          >
            <span class="icon">{{ mode.icon }}</span>
            {{ mode.label }}
          </div>
        </div>
      </div>

      <div class="setting-group">
        <label>粒子预设</label>
        <div class="preset-grid">
          <div
            v-for="p in presets"
            :key="p.id"
            class="preset-btn"
            :class="{ active: currentPreset === p.id }"
            @click="setPreset(p.id)"
          >
            <span class="icon">{{ p.icon }}</span>
            {{ p.label }}
          </div>
        </div>
      </div>

      <div class="setting-group">
        <label>粒子数量上限: {{ maxParticles }}</label>
        <input type="range" min="500" max="8000" step="500" v-model.number="maxParticles">
      </div>

      <div class="setting-group">
        <label>粒子大小: {{ baseSize }}</label>
        <input type="range" min="1" max="8" v-model.number="baseSize">
      </div>

      <div class="setting-group">
        <label>力场强度: {{ forceStrength }}</label>
        <input type="range" min="1" max="15" v-model.number="forceStrength">
      </div>

      <div class="setting-group">
        <label>拖尾: {{ (trailAlpha).toFixed(2) }}</label>
        <input type="range" min="1" max="50" :value="trailAlphaRaw" @input="onTrailInput">
      </div>

      <div id="cameraSelectorContainer" ref="cameraSelectorContainer"></div>

      <div class="controls">
        <button :class="{ primary: !isRunning }" @click="toggleCamera" :disabled="btnDisabled">
          {{ btnText }}
        </button>
        <button @click="takePhoto">拍照</button>
        <button @click="clearScreen">清屏</button>
      </div>

      <div style="font-size:11px; color:#555;">{{ fpsText }}</div>

      <div class="tip-box">
        <b>手势说明:</b><br>
        指尖发射 - 五指张开，粒子从指尖喷射<br>
        引力场 - 张开手掌吸引粒子<br>
        斥力场 - 握拳推开粒子<br>
        漩涡 - 捏合手势制造漩涡<br>
        自由绘制 - 食指指向画出持久粒子轨迹<br>
        粒子球 - 张开散开/握拳压缩/捏合旋转/食指吸引
      </div>
    </div>

    <div class="main">
      <div class="status-bar">
        <span>{{ statusText }}</span>
        <span>{{ gestureName }}</span>
      </div>
      <div class="gesture-indicator" :style="{ opacity: gestureOpacity }">
        {{ gestureIcon }}
      </div>
      <video ref="videoRef" autoplay playsinline style="display:none;"></video>
      <canvas ref="canvasRef"></canvas>
      <div class="hand-preview" :style="{ display: handPreviewDisplay }">
        <canvas ref="handCanvasRef" width="200" height="150"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { HandLandmarker, FilesetResolver } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs'
import { useCamera } from '../../composables/useCamera.js'

const { stream, isRunning, startCamera: cameraStart, stopCamera: cameraStop, initCameraSelector, getSelectedStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const handCanvasRef = ref(null)
const cameraSelectorContainer = ref(null)

const btnText = ref('开启摄像头')
const btnDisabled = ref(false)
const fpsText = ref('FPS: -- | 粒子: 0')
const statusText = ref('等待开启摄像头')
const gestureName = ref('')
const gestureIcon = ref('🖐️')
const gestureOpacity = ref(0)
const handPreviewDisplay = ref('none')

const interactionMode = ref('emit')
const currentPreset = ref('fire')
const maxParticles = ref(2000)
const baseSize = ref(3)
const forceStrength = ref(5)
const trailAlpha = ref(0.10)
const trailAlphaRaw = ref(10)

let handLandmarker = null
let animId = null
let frameCount = 0
let lastFpsTime = performance.now()
let particles = []
let drawParticles = []
let handData = null
let prevHandData = null
let orbParticles = []
let orbInitialized = false
let localStream = null

const modes = [
  { id: 'emit', icon: '✨', label: '指尖发射' },
  { id: 'attract', icon: '🌀', label: '引力场' },
  { id: 'repel', icon: '💥', label: '斥力场' },
  { id: 'vortex', icon: '🌪️', label: '漩涡' },
  { id: 'draw', icon: '✏️', label: '自由绘制' },
  { id: 'orb', icon: '🔮', label: '粒子球' }
]

const presets = [
  { id: 'fire', icon: '🔥', label: '火焰' },
  { id: 'neon', icon: '💜', label: '霓虹' },
  { id: 'rainbow', icon: '🌈', label: '彩虹' },
  { id: 'matrix', icon: '💚', label: '矩阵' },
  { id: 'stars', icon: '⭐', label: '星空' },
  { id: 'ice', icon: '❄️', label: '冰晶' }
]

const PRESETS = {
  fire: {
    colors: ['#ff4500', '#ff6600', '#ff8800', '#ffaa00', '#ffcc00', '#fff200'],
    bg: 'rgba(0,0,0,α)'
  },
  neon: {
    colors: ['#ff00ff', '#ff00aa', '#cc00ff', '#aa00ff', '#ff0066'],
    bg: 'rgba(0,0,0,α)'
  },
  rainbow: {
    colors: ['#ff0000', '#ff8800', '#ffff00', '#00ff00', '#0088ff', '#8800ff', '#ff00ff'],
    bg: 'rgba(0,0,0,α)'
  },
  matrix: {
    colors: ['#00ff00', '#00cc00', '#009900', '#00ff66'],
    bg: 'rgba(0,3,0,α)'
  },
  stars: {
    colors: ['#ffffff', '#aaddff', '#ffddaa', '#ddddff'],
    bg: 'rgba(0,0,5,α)'
  },
  ice: {
    colors: ['#aaddff', '#88ccff', '#66bbff', '#ffffff', '#ddeeff'],
    bg: 'rgba(0,3,5,α)'
  }
}

const glowCache = {}

function getGlowTexture(color, size) {
  const key = color + '|' + size
  if (glowCache[key]) return glowCache[key]
  const r = size * 3
  const s = r * 2
  const c = document.createElement('canvas')
  c.width = s; c.height = s
  const cx = c.getContext('2d')
  const grad = cx.createRadialGradient(r, r, 0, r, r, r)
  grad.addColorStop(0, color)
  grad.addColorStop(0.4, color + 'aa')
  grad.addColorStop(1, 'transparent')
  cx.fillStyle = grad
  cx.fillRect(0, 0, s, s)
  glowCache[key] = c
  return c
}

class Particle {
  constructor(x, y, vx, vy, color) {
    this.x = x
    this.y = y
    this.vx = vx || (Math.random() - 0.5) * 2
    this.vy = vy || (Math.random() - 0.5) * 2
    this.life = 1
    this.decay = 0.008 + Math.random() * 0.012
    this.size = baseSize.value * (0.5 + Math.random())
    this.color = color || this.randomColor()
  }

  randomColor() {
    const colors = PRESETS[currentPreset.value].colors
    return colors[Math.floor(Math.random() * colors.length)]
  }

  update() {
    this.x += this.vx
    this.y += this.vy
    this.vx *= 0.98
    this.vy *= 0.98
    this.vy += 0.02
    this.life -= this.decay
  }
}

class DrawParticle {
  constructor(x, y, color) {
    this.x = x
    this.y = y
    this.vx = 0
    this.vy = 0
    this.life = 1
    this.decay = 0.0003
    this.size = baseSize.value * (0.6 + Math.random() * 0.4)
    this.color = color || this.randomColor()
  }

  randomColor() {
    const colors = PRESETS[currentPreset.value].colors
    return colors[Math.floor(Math.random() * colors.length)]
  }

  update() {
    this.life -= this.decay
  }
}

function initOrb(cx, cy) {
  orbParticles = []
  const radius = 120
  const count = 300
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    const r = radius * (0.3 + Math.random() * 0.7)
    orbParticles.push({
      baseX: Math.cos(theta) * Math.sin(phi) * r,
      baseY: Math.sin(theta) * Math.sin(phi) * r,
      baseZ: Math.cos(phi) * r,
      x: cx + Math.cos(theta) * Math.sin(phi) * r,
      y: cy + Math.sin(theta) * Math.sin(phi) * r,
      z: Math.cos(phi) * r,
      vx: 0, vy: 0,
      size: 1.5 + Math.random() * 2,
      color: PRESETS[currentPreset.value].colors[Math.floor(Math.random() * PRESETS[currentPreset.value].colors.length)]
    })
  }
  orbInitialized = true
}

function detectGesture(lm) {
  const tips = [4, 8, 12, 16, 20]
  const pips = [3, 6, 10, 14, 18]

  let fingersUp = 0
  if (lm[4].x < lm[3].x) fingersUp++
  for (let i = 1; i < 5; i++) {
    if (lm[tips[i]].y < lm[pips[i]].y) fingersUp++
  }

  const thumbTip = lm[4]
  const indexTip = lm[8]
  const pinchDist = Math.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y)

  let gesture = 'none'
  let icon = '✋'

  if (pinchDist < 0.05) {
    gesture = 'pinch'
    icon = '🤏'
  } else if (fingersUp === 0) {
    gesture = 'fist'
    icon = '✊'
  } else if (fingersUp === 1 && lm[8].y < lm[6].y) {
    gesture = 'point'
    icon = '☝️'
  } else if (fingersUp >= 4) {
    gesture = 'open'
    icon = '🖐️'
  } else {
    gesture = 'partial'
    icon = '🖖'
  }

  return { gesture, icon, fingersUp, pinchDist }
}

function getFingertips(lm, w, h) {
  return [4, 8, 12, 16, 20].map(i => ({
    x: (1 - lm[i].x) * w,
    y: lm[i].y * h
  }))
}

function getHandCenter(lm, w, h) {
  let cx = 0, cy = 0
  for (const p of lm) {
    cx += (1 - p.x) * w
    cy += p.y * h
  }
  return { x: cx / lm.length, y: cy / lm.length }
}

function getHandVelocity(lm, prevLm, w, h) {
  if (!prevLm) return { vx: 0, vy: 0 }
  const curr = getHandCenter(lm, w, h)
  const prev = getHandCenter(prevLm, w, h)
  return { vx: (curr.x - prev.x) * 0.3, vy: (curr.y - prev.y) * 0.3 }
}

function applyInteraction(gesture, lm, w, h) {
  const center = getHandCenter(lm, w, h)
  const tips = getFingertips(lm, w, h)
  const vel = getHandVelocity(lm, prevHandData?.landmarks, w, h)
  const force = forceStrength.value

  switch (interactionMode.value) {
    case 'emit':
      if (gesture === 'open' || gesture === 'partial') {
        for (const tip of tips) {
          for (let i = 0; i < 3; i++) {
            const angle = Math.random() * Math.PI * 2
            const speed = 1 + Math.random() * force * 0.5
            particles.push(new Particle(
              tip.x + (Math.random() - 0.5) * 10,
              tip.y + (Math.random() - 0.5) * 10,
              Math.cos(angle) * speed + vel.vx,
              Math.sin(angle) * speed + vel.vy - 1
            ))
          }
        }
      }
      break

    case 'attract':
      if (gesture === 'open') {
        for (const p of particles) {
          const dx = center.x - p.x
          const dy = center.y - p.y
          const dist = Math.hypot(dx, dy)
          if (dist < 250 && dist > 5) {
            const f = force / dist
            p.vx += dx * f * 0.1
            p.vy += dy * f * 0.1
          }
        }
      } else {
        for (const tip of tips) {
          for (let i = 0; i < 2; i++) {
            particles.push(new Particle(
              tip.x + (Math.random() - 0.5) * 8,
              tip.y + (Math.random() - 0.5) * 8,
              (Math.random() - 0.5) * 3,
              (Math.random() - 0.5) * 3
            ))
          }
        }
      }
      break

    case 'repel':
      if (gesture === 'fist') {
        for (const p of particles) {
          const dx = p.x - center.x
          const dy = p.y - center.y
          const dist = Math.hypot(dx, dy)
          if (dist < 200 && dist > 5) {
            const f = force / dist
            p.vx += dx * f * 0.3
            p.vy += dy * f * 0.3
          }
        }
      } else {
        for (const tip of tips) {
          for (let i = 0; i < 2; i++) {
            particles.push(new Particle(
              tip.x + (Math.random() - 0.5) * 8,
              tip.y + (Math.random() - 0.5) * 8,
              (Math.random() - 0.5) * 2,
              (Math.random() - 0.5) * 2
            ))
          }
        }
      }
      break

    case 'vortex':
      for (const p of particles) {
        const dx = p.x - center.x
        const dy = p.y - center.y
        const dist = Math.hypot(dx, dy)
        if (dist < 200 && dist > 5) {
          const angle = Math.atan2(dy, dx)
          const tangentAngle = angle + Math.PI / 2
          const pull = gesture === 'pinch' ? force * 0.15 : force * 0.05
          const spin = gesture === 'pinch' ? force * 0.2 : force * 0.1
          const falloff = 1 - dist / 200
          p.vx += Math.cos(tangentAngle) * spin * falloff + dx * pull * 0.01
          p.vy += Math.sin(tangentAngle) * spin * falloff + dy * pull * 0.01
        }
      }
      for (let i = 0; i < 2; i++) {
        const angle = Math.random() * Math.PI * 2
        const r = 20 + Math.random() * 40
        particles.push(new Particle(
          center.x + Math.cos(angle) * r,
          center.y + Math.sin(angle) * r,
          Math.cos(angle + Math.PI / 2) * 2,
          Math.sin(angle + Math.PI / 2) * 2
        ))
      }
      break

    case 'draw':
      if (gesture === 'point') {
        const tip = tips[1]
        for (let i = 0; i < 8; i++) {
          drawParticles.push(new DrawParticle(
            tip.x + (Math.random() - 0.5) * 3,
            tip.y + (Math.random() - 0.5) * 3
          ))
        }
      }
      break

    case 'orb':
      if (!orbInitialized) {
        initOrb(w / 2, h / 2)
      }
      if (gesture === 'open') {
        for (const op of orbParticles) {
          const dx = op.x - center.x
          const dy = op.y - center.y
          const dist = Math.hypot(dx, dy)
          if (dist < 300 && dist > 5) {
            const f = force / dist * 2
            op.vx += dx * f
            op.vy += dy * f
          }
        }
      } else if (gesture === 'fist') {
        for (const op of orbParticles) {
          const dx = center.x - op.x
          const dy = center.y - op.y
          const dist = Math.hypot(dx, dy)
          if (dist > 5) {
            const f = force / dist * 1.5
            op.vx += dx * f
            op.vy += dy * f
          }
        }
      } else if (gesture === 'pinch') {
        for (const op of orbParticles) {
          const dx = op.x - center.x
          const dy = op.y - center.y
          const angle = Math.atan2(dy, dx)
          const tangentAngle = angle + Math.PI / 2
          op.vx += Math.cos(tangentAngle) * force * 0.8
          op.vy += Math.sin(tangentAngle) * force * 0.8
        }
      } else if (gesture === 'point') {
        const tip = tips[1]
        for (const op of orbParticles) {
          const dx = tip.x - op.x
          const dy = tip.y - op.y
          const dist = Math.hypot(dx, dy)
          if (dist < 200 && dist > 5) {
            const f = force / dist * 3
            op.vx += dx * f
            op.vy += dy * f
          }
        }
      }
      break
  }
}

function spawnAmbient() {
  if (particles.length < 50 && handData) {
    const canvas = canvasRef.value
    const w = canvas.width, h = canvas.height
    for (let i = 0; i < 3; i++) {
      particles.push(new Particle(
        Math.random() * w,
        Math.random() * h,
        (Math.random() - 0.5) * 0.5,
        (Math.random() - 0.5) * 0.5
      ))
    }
  }
}

async function initHandLandmarker() {
  statusText.value = '加载手势模型...'
  try {
    const vision = await FilesetResolver.forVisionTasks(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
    )
    handLandmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',
        delegate: 'GPU'
      },
      runningMode: 'VIDEO',
      numHands: 2,
      minHandDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    })
    statusText.value = '运行中'
    return true
  } catch (e) {
    console.error(e)
    statusText.value = '模型加载失败: ' + e.message
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

    const canvas = canvasRef.value
    canvas.width = window.innerWidth - 260
    canvas.height = window.innerHeight

    if (!handLandmarker) {
      const ok = await initHandLandmarker()
      if (!ok) {
        btnText.value = '开启摄像头'
        btnDisabled.value = false
        return
      }
    }

    handPreviewDisplay.value = 'block'
    isRunning.value = true
    btnText.value = '关闭摄像头'
    btnDisabled.value = false
    statusText.value = '运行中'
    frameCount = 0
    lastFpsTime = performance.now()
    processFrame()
  } catch (e) {
    console.error('启动失败:', e)
    statusText.value = '错误: ' + e.message
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
  handData = null
  prevHandData = null
  orbParticles = []
  orbInitialized = false
  handPreviewDisplay.value = 'none'
  isRunning.value = false
  btnText.value = '开启摄像头'
  btnDisabled.value = false
  gestureOpacity.value = 0
  statusText.value = '已停止'
}

function toggleCamera() {
  isRunning.value ? stopCamera() : startCamera()
}

function processFrame() {
  if (!localStream || !handLandmarker) return
  animId = requestAnimationFrame(processFrame)

  if (videoRef.value.readyState < 2) return

  const now = performance.now()
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  const w = canvas.width
  const h = canvas.height

  prevHandData = handData
  handData = null

  try {
    const results = handLandmarker.detectForVideo(videoRef.value, now)

    const handCanvas = handCanvasRef.value
    const handCtx = handCanvas.getContext('2d')
    handCtx.save()
    handCtx.translate(200, 0)
    handCtx.scale(-1, 1)
    handCtx.drawImage(videoRef.value, 0, 0, 200, 150)
    handCtx.restore()

    if (results && results.landmarks && results.landmarks.length > 0) {
      handData = {
        landmarks: results.landmarks[0],
        handedness: results.handedness?.[0]?.[0]?.categoryName || 'Right'
      }

      const lm = handData.landmarks
      const gestureInfo = detectGesture(lm)

      gestureIcon.value = gestureInfo.icon
      gestureOpacity.value = 1
      gestureName.value = gestureInfo.gesture

      applyInteraction(gestureInfo.gesture, lm, w, h)

      for (let i = 1; i < results.landmarks.length; i++) {
        const lm2 = results.landmarks[i]
        const gestureInfo2 = detectGesture(lm2)
        applyInteraction(gestureInfo2.gesture, lm2, w, h)
      }
    } else {
      gestureOpacity.value = 0
      gestureName.value = ''
    }
  } catch (e) {
    console.warn('detectForVideo error:', e)
  }

  spawnAmbient()

  ctx.fillStyle = PRESETS[currentPreset.value].bg.replace('α', trailAlpha.value)
  ctx.fillRect(0, 0, w, h)

  let alive = 0
  ctx.globalCompositeOperation = 'lighter'

  for (let i = drawParticles.length - 1; i >= 0; i--) {
    const p = drawParticles[i]
    p.update()
    if (p.life <= 0) {
      drawParticles[i] = drawParticles[drawParticles.length - 1]
      drawParticles.pop()
      continue
    }
    alive++
    const alpha = Math.min(p.life, 1)
    const r = p.size * Math.min(p.life * 3, 1)
    if (r <= 0) continue
    ctx.globalAlpha = alpha
    ctx.fillStyle = p.color
    ctx.beginPath()
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2)
    ctx.fill()
  }

  if (interactionMode.value === 'orb' && orbInitialized) {
    for (const op of orbParticles) {
      const dx = op.baseX - (op.x - w / 2)
      const dy = op.baseY - (op.y - h / 2)
      op.vx += dx * 0.02
      op.vy += dy * 0.02
      op.vx *= 0.92
      op.vy *= 0.92
      op.x += op.vx
      op.y += op.vy
      const alpha = 0.5 + (op.z + 120) / 240 * 0.5
      const sizeMul = 0.5 + (op.z + 120) / 240 * 0.5
      ctx.globalAlpha = alpha
      ctx.fillStyle = op.color
      ctx.beginPath()
      ctx.arc(op.x, op.y, op.size * sizeMul, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.update()
    if (p.life <= 0) {
      particles[i] = particles[particles.length - 1]
      particles.pop()
      continue
    }
    if (p.x < -50 || p.x > w + 50 || p.y < -50 || p.y > h + 50) {
      particles[i] = particles[particles.length - 1]
      particles.pop()
      continue
    }
    alive++
    const alpha = p.life
    const r = p.size * alpha
    if (r <= 0) continue

    const tex = getGlowTexture(p.color, Math.ceil(r))
    ctx.globalAlpha = alpha * 0.5
    ctx.drawImage(tex, p.x - tex.width / 2, p.y - tex.height / 2)

    ctx.globalAlpha = alpha
    ctx.fillStyle = p.color
    ctx.beginPath()
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalCompositeOperation = 'source-over'
  ctx.globalAlpha = 1

  while (particles.length < maxParticles.value * 0.1 && handData && interactionMode.value !== 'draw' && interactionMode.value !== 'orb') {
    const lm = handData.landmarks
    const center = getHandCenter(lm, w, h)
    particles.push(new Particle(
      center.x + (Math.random() - 0.5) * 100,
      center.y + (Math.random() - 0.5) * 100,
      (Math.random() - 0.5) * 2,
      (Math.random() - 0.5) * 2
    ))
  }

  if (drawParticles.length > 5000) {
    drawParticles.splice(0, drawParticles.length - 5000)
  }

  frameCount++
  if (now - lastFpsTime > 1000) {
    fpsText.value = `FPS: ${frameCount} | 粒子: ${alive + orbParticles.length}`
    frameCount = 0
    lastFpsTime = now
  }
}

function setMode(mode) {
  interactionMode.value = mode
  if (mode !== 'orb') {
    orbParticles = []
    orbInitialized = false
  }
}

function setPreset(preset) {
  currentPreset.value = preset
  for (const key in glowCache) delete glowCache[key]
  particles.forEach(p => {
    const colors = PRESETS[preset].colors
    p.color = colors[Math.floor(Math.random() * colors.length)]
  })
}

function onTrailInput(e) {
  trailAlphaRaw.value = parseInt(e.target.value)
  trailAlpha.value = trailAlphaRaw.value / 100
}

function takePhoto() {
  const link = document.createElement('a')
  link.download = 'gesture_particle_' + Date.now() + '.png'
  link.href = canvasRef.value.toDataURL()
  link.click()
}

function clearScreen() {
  particles = []
  drawParticles = []
  orbParticles = []
  orbInitialized = false
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#000'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
}

function onResize() {
  if (localStream) {
    canvasRef.value.width = window.innerWidth - 260
    canvasRef.value.height = window.innerHeight
  }
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

  const canvas = canvasRef.value
  canvas.width = window.innerWidth - 260
  canvas.height = window.innerHeight
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#000'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  window.addEventListener('resize', onResize)
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
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.particle-art {
  font-family: -apple-system, sans-serif;
  background: #000;
  color: #e0e0e0;
  min-height: 100vh;
  display: flex;
}

.sidebar {
  width: 260px;
  background: rgba(10,10,10,0.95);
  border-right: 1px solid #222;
  padding: 16px;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  z-index: 10;
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
  position: relative;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.preset-btn {
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

.preset-btn:hover {
  border-color: #444;
}

.preset-btn.active {
  border-color: #667eea;
  background: #1a1a3a;
  color: #fff;
}

.preset-btn .icon {
  font-size: 20px;
  display: block;
  margin-bottom: 2px;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.mode-btn {
  padding: 6px;
  background: #1a1a1a;
  border: 2px solid #2a2a2a;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  font-size: 11px;
  color: #aaa;
  transition: all 0.15s;
}

.mode-btn:hover {
  border-color: #444;
}

.mode-btn.active {
  border-color: #ff6b6b;
  background: #2a1a1a;
  color: #fff;
}

.mode-btn .icon {
  font-size: 16px;
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

.status-bar {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.6);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  color: #aaa;
  z-index: 5;
  display: flex;
  gap: 16px;
}

.gesture-indicator {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.7);
  padding: 10px 24px;
  border-radius: 12px;
  font-size: 20px;
  z-index: 5;
  transition: all 0.2s;
}

.hand-preview {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 200px;
  height: 150px;
  border: 2px solid #333;
  border-radius: 8px;
  overflow: hidden;
  z-index: 5;
}

.hand-preview canvas {
  width: 100%;
  height: 100%;
}

.tip-box {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 10px;
  font-size: 11px;
  color: #666;
  line-height: 1.6;
}
</style>