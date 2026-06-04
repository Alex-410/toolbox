<template>
  <div class="game-root">
    <router-link to="/camera" class="back-link">&larr; 返回工具集</router-link>

    <video ref="videoRef" autoplay playsinline style="display:none;"></video>
    <canvas ref="canvasRef" class="game-canvas"></canvas>

    <div class="sidebar">
      <div ref="cameraSelectorContainer" id="cameraSelectorContainer"></div>
    </div>

    <div class="hud">
      <div class="hud-item">
        <div class="label">得分</div>
        <div class="value">{{ score }}</div>
      </div>
      <div class="hud-item">
        <div class="label">时间</div>
        <div class="value">{{ timeLeft }}</div>
      </div>
      <div class="hud-item">
        <div class="label">连击</div>
        <div class="value">{{ comboText }}</div>
      </div>
    </div>

    <div class="gesture-indicator">
      <div class="gesture-icon">{{ gestureIcon }}</div>
      <div class="gesture-text">{{ gestureText }}</div>
    </div>

    <div class="controls-hud">
      <button class="btn primary" @click="beginGame">开始游戏</button>
      <button class="btn" @click="endGame">重新开始</button>
    </div>

    <div class="mini-cam" v-show="miniCamVisible">
      <canvas ref="camPreviewRef" width="200" height="150"></canvas>
    </div>

    <div class="calibrate-bar" v-show="calibrating">
      <h2>📐 校准中...</h2>
      <p>请站好，双手自然下垂</p>
      <div class="progress-bar"><div class="fill" :style="{ width: calibratePercent + '%' }"></div></div>
    </div>

    <div class="hint-bar" v-show="hintVisible">{{ hintText }}</div>

    <div class="game-overlay" v-show="startOverlayVisible">
      <h1>🏃 体感收集游戏</h1>
      <p>用身体控制角色，收集从天而降的金币和星星！</p>
      <div class="tutorial-gestures">
        <div class="tutorial-item">
          <span class="icon">👈🦱</span>
          <div class="label">左手向左伸</div>
          <div class="desc">角色向左移动</div>
        </div>
        <div class="tutorial-item">
          <span class="icon">🦱👉</span>
          <div class="label">右手向右伸</div>
          <div class="desc">角色向右移动</div>
        </div>
        <div class="tutorial-item">
          <span class="icon">🦘</span>
          <div class="label">身体/头向上</div>
          <div class="desc">角色跳跃</div>
        </div>
      </div>
      <button class="primary play-btn" @click="beginGame">开始游戏</button>
    </div>

    <div class="game-overlay" v-show="endOverlayVisible">
      <h1>游戏结束</h1>
      <div class="score-display">{{ score }}</div>
      <p>{{ finalMsg }}</p>
      <button class="primary play-btn" @click="startGame">再来一局</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { PoseLandmarker, FilesetResolver } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.mjs'
import { useCamera } from '../../composables/useCamera.js'

const { initCameraSelector, getSelectedStream, stream: cameraStream } = useCamera()

const videoRef = ref(null)
const canvasRef = ref(null)
const camPreviewRef = ref(null)
const cameraSelectorContainer = ref(null)

const score = ref(0)
const timeLeft = ref(60)
const comboText = ref('x1')
const gestureIcon = ref('🧍')
const gestureText = ref('站立')
const miniCamVisible = ref(false)
const calibrating = ref(false)
const calibratePercent = ref(0)
const hintVisible = ref(false)
const hintText = ref('')
const startOverlayVisible = ref(true)
const endOverlayVisible = ref(false)
const finalMsg = ref('干得漂亮！')

let poseLandmarker = null
let gameRunning = false
let combo = 1
let timerInterval = null
let animId = null
let gameAnimId = null

let player = { x: 0.5, targetX: 0.5, jumping: false, jumpY: 0, jumpVel: 0, grounded: true }
let items = []
let particles = []

let smoothedLm = null
const SMOOTH = 0.35

let calibrationData = null
const CALIBRATE_DURATION = 60
let calibrateFrames = 0
let calibrateSamples = []

let poseDetected = false
let localStream = null

let ctx = null
let camCtx = null

async function initModel() {
  const vision = await FilesetResolver.forVisionTasks(
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
  )
  const modelCandidates = [
    'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task',
    'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task',
    'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task'
  ]
  for (const modelPath of modelCandidates) {
    try {
      poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
        baseOptions: { modelAssetPath: modelPath, delegate: 'GPU' },
        runningMode: 'VIDEO',
        numPoses: 1
      })
      return
    } catch (e) {
      console.warn('模型加载失败:', modelPath, e.message)
    }
  }
  throw new Error('All pose model sources failed.')
}

function smoothLandmarks(lm) {
  if (!smoothedLm) {
    smoothedLm = lm.map(p => ({ x: p.x, y: p.y, z: p.z }))
    return smoothedLm
  }
  for (let i = 0; i < lm.length; i++) {
    smoothedLm[i].x += (lm[i].x - smoothedLm[i].x) * SMOOTH
    smoothedLm[i].y += (lm[i].y - smoothedLm[i].y) * SMOOTH
    smoothedLm[i].z += (lm[i].z - smoothedLm[i].z) * SMOOTH
  }
  return smoothedLm
}

async function startCameraFn() {
  try {
    localStream = await getSelectedStream()
    videoRef.value.srcObject = localStream
    await new Promise((resolve, reject) => {
      videoRef.value.onloadedmetadata = () => videoRef.value.play().then(resolve).catch(reject)
      videoRef.value.onerror = reject
      setTimeout(() => reject(new Error('视频加载超时')), 10000)
    })
    if (!poseLandmarker) await initModel()
    miniCamVisible.value = true
    processFrame()
  } catch (e) {
    console.error('启动失败:', e)
  }
}

function processFrame() {
  if (!localStream || !poseLandmarker) return
  animId = requestAnimationFrame(processFrame)
  if (videoRef.value.readyState < 2) return
  const now = performance.now()
  let results = null
  try {
    results = poseLandmarker.detectForVideo(videoRef.value, now)
  } catch (e) {
    console.warn('detectForVideo error:', e)
    return
  }
  drawCamPreview(results)
  if (results && results.landmarks && results.landmarks.length > 0) {
    const rawLm = results.landmarks[0]
    const lm = smoothLandmarks(rawLm)
    poseDetected = true
    if (calibrating.value) {
      handleCalibration(lm)
    } else {
      handleGestures(lm)
    }
  } else {
    poseDetected = false
  }
}

function drawCamPreview(results) {
  camCtx.save()
  camCtx.translate(200, 0)
  camCtx.scale(-1, 1)
  camCtx.drawImage(videoRef.value, 0, 0, 200, 150)
  camCtx.restore()
  if (results && results.landmarks && results.landmarks.length > 0) {
    const lm = results.landmarks[0]
    const connections = [
      [11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24]
    ]
    camCtx.strokeStyle = '#00ff88'
    camCtx.lineWidth = 1.5
    for (const [a, b] of connections) {
      camCtx.beginPath()
      camCtx.moveTo((1 - lm[a].x) * 200, lm[a].y * 150)
      camCtx.lineTo((1 - lm[b].x) * 200, lm[b].y * 150)
      camCtx.stroke()
    }
    const keyPoints = [0, 11, 12, 13, 14, 15, 16, 23, 24]
    for (const i of keyPoints) {
      const sx = (1 - lm[i].x) * 200
      const sy = lm[i].y * 150
      camCtx.fillStyle = i === 0 ? '#ff4444' : '#00ff88'
      camCtx.beginPath()
      camCtx.arc(sx, sy, 3, 0, Math.PI * 2)
      camCtx.fill()
    }
  }
}

function handleCalibration(lm) {
  calibrateSamples.push({
    lShoulderY: lm[11].y,
    rShoulderY: lm[12].y,
    noseY: lm[0].y,
    lWristX: lm[15].x,
    rWristX: lm[16].x,
    lWristY: lm[15].y,
    rWristY: lm[16].y
  })
  calibrateFrames++
  calibratePercent.value = Math.min(100, Math.round(calibrateFrames / CALIBRATE_DURATION * 100))
  if (calibrateFrames >= CALIBRATE_DURATION) {
    finishCalibration()
  }
}

function finishCalibration() {
  const n = calibrateSamples.length
  const avg = (key) => calibrateSamples.reduce((s, v) => s + v[key], 0) / n
  calibrationData = {
    shoulderY: (avg('lShoulderY') + avg('rShoulderY')) / 2,
    noseY: avg('noseY'),
    noseShoulderDiff: avg('noseY') - (avg('lShoulderY') + avg('rShoulderY')) / 2,
    wristRestX: (avg('lWristX') + avg('rWristX')) / 2,
    lWristRestX: avg('lWristX'),
    rWristRestX: avg('rWristX'),
    lWristRestY: avg('lWristY'),
    rWristRestY: avg('rWristY')
  }
  calibrating.value = false
  hintVisible.value = true
  hintText.value = '校准完成！开始游戏吧'
  setTimeout(() => { hintVisible.value = false }, 2000)
}

function handleGestures(lm) {
  if (!calibrationData) return
  const lWrist = lm[15]
  const rWrist = lm[16]
  const lShoulder = lm[11]
  const rShoulder = lm[12]
  const nose = lm[0]
  const shoulderY = (lShoulder.y + rShoulder.y) / 2
  const currentNoseDiff = nose.y - shoulderY
  const baselineNoseDiff = calibrationData.noseShoulderDiff
  const noseRise = baselineNoseDiff - currentNoseDiff
  const isJumping = noseRise > 0.06
  const lReachX = calibrationData.lWristRestX - lWrist.x
  const rReachX = rWrist.x - calibrationData.rWristRestX
  const reachThreshold = 0.05
  const reachMax = 0.20
  let moveDir = 0
  if (lReachX > reachThreshold) {
    const intensity = Math.min(1, (lReachX - reachThreshold) / (reachMax - reachThreshold))
    moveDir = -intensity
  }
  if (rReachX > reachThreshold) {
    const intensity = Math.min(1, (rReachX - reachThreshold) / (reachMax - reachThreshold))
    moveDir = Math.max(moveDir, intensity)
  }
  if (Math.abs(moveDir) > 0.01) {
    const speed = 0.008 + Math.abs(moveDir) * 0.015
    player.targetX = Math.max(0.08, Math.min(0.92, player.targetX + moveDir * speed))
  }
  if (isJumping && player.grounded) {
    player.jumping = true
    player.grounded = false
    player.jumpVel = -10
  }
  let gesture = 'stand'
  let icon = '🧍'
  if (isJumping) {
    gesture = 'jump'; icon = '🦘'
  } else if (moveDir < -0.3) {
    gesture = 'left_fast'; icon = '⬅️'
  } else if (moveDir < -0.05) {
    gesture = 'left'; icon = '👈'
  } else if (moveDir > 0.3) {
    gesture = 'right_fast'; icon = '➡️'
  } else if (moveDir > 0.05) {
    gesture = 'right'; icon = '👉'
  }
  gestureIcon.value = icon
  gestureText.value = { stand: '站立', left: '向左', left_fast: '快速向左', right: '向右', right_fast: '快速向右', jump: '跳跃！' }[gesture]
}

function gameLoop() {
  if (!gameRunning) return
  const canvas = canvasRef.value
  ctx.fillStyle = '#0a0a1a'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  for (let i = 0; i < 50; i++) {
    const x = (Math.sin(i * 137.5) * 0.5 + 0.5) * canvas.width
    const y = (Math.cos(i * 97.3) * 0.5 + 0.5) * canvas.height
    const r = 0.5 + Math.sin(Date.now() * 0.001 + i) * 0.5
    ctx.fillStyle = `rgba(255,255,255,${0.3 + r * 0.4})`
    ctx.beginPath()
    ctx.arc(x, y, r * 1.5, 0, Math.PI * 2)
    ctx.fill()
  }
  player.x += (player.targetX - player.x) * 0.12
  if (!player.grounded) {
    player.jumpVel += 0.6
    player.jumpY += player.jumpVel
    if (player.jumpY >= 0) {
      player.jumpY = 0
      player.jumpVel = 0
      player.grounded = true
      player.jumping = false
    }
  }
  const px = player.x * canvas.width
  const py = canvas.height * 0.85 + player.jumpY
  drawPlayer(px, py)
  if (Math.random() < 0.03) {
    items.push({
      x: Math.random() * canvas.width,
      y: -20,
      vy: 1 + Math.random() * 2,
      type: Math.random() < 0.2 ? 'star' : 'coin',
      size: 15 + Math.random() * 10,
      rotation: 0
    })
  }
  for (let i = items.length - 1; i >= 0; i--) {
    const item = items[i]
    item.y += item.vy
    item.rotation += 0.05
    const dx = px - item.x
    const dy = py - item.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < 50) {
      const points = item.type === 'star' ? 50 : 10
      score.value += points * combo
      combo = Math.min(combo + 1, 10)
      comboText.value = 'x' + combo
      for (let j = 0; j < 8; j++) {
        particles.push({
          x: item.x, y: item.y,
          vx: (Math.random() - 0.5) * 6,
          vy: (Math.random() - 0.5) * 6,
          life: 1,
          color: item.type === 'star' ? '#ffeb3b' : '#ff9800'
        })
      }
      items.splice(i, 1)
      continue
    }
    if (item.y > canvas.height + 20) {
      combo = 1
      comboText.value = 'x1'
      items.splice(i, 1)
      continue
    }
    drawItem(item)
  }
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.x += p.vx
    p.y += p.vy
    p.life -= 0.03
    if (p.life <= 0) { particles.splice(i, 1); continue }
    ctx.globalAlpha = p.life
    ctx.fillStyle = p.color
    ctx.beginPath()
    ctx.arc(p.x, p.y, 3 * p.life, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(0, canvas.height * 0.88)
  ctx.lineTo(canvas.width, canvas.height * 0.88)
  ctx.stroke()
  gameAnimId = requestAnimationFrame(gameLoop)
}

function drawPlayer(x, y) {
  ctx.save()
  ctx.translate(x, y)
  ctx.fillStyle = '#4caf50'
  ctx.beginPath()
  ctx.ellipse(0, 0, 20, 30, 0, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#ffcc80'
  ctx.beginPath()
  ctx.arc(0, -40, 15, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#333'
  ctx.beginPath()
  ctx.arc(-5, -43, 2, 0, Math.PI * 2)
  ctx.arc(5, -43, 2, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = '#4caf50'
  ctx.lineWidth = 4
  const armDown = player.grounded && !player.jumping
  if (armDown) {
    ctx.beginPath(); ctx.moveTo(-20, -10); ctx.lineTo(-30, 10); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(20, -10); ctx.lineTo(30, 10); ctx.stroke()
  } else {
    ctx.beginPath(); ctx.moveTo(-20, -10); ctx.lineTo(-35, -30); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(20, -10); ctx.lineTo(35, -30); ctx.stroke()
  }
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 4
  if (player.jumping) {
    ctx.beginPath(); ctx.moveTo(-8, 25); ctx.lineTo(-18, 40); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(8, 25); ctx.lineTo(18, 40); ctx.stroke()
  } else {
    ctx.beginPath(); ctx.moveTo(-8, 25); ctx.lineTo(-12, 50); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(8, 25); ctx.lineTo(12, 50); ctx.stroke()
  }
  ctx.restore()
}

function drawItem(item) {
  ctx.save()
  ctx.translate(item.x, item.y)
  ctx.rotate(item.rotation)
  if (item.type === 'star') {
    ctx.fillStyle = '#ffeb3b'
    drawStarShape(0, 0, item.size)
  } else {
    ctx.fillStyle = '#ff9800'
    ctx.beginPath()
    ctx.arc(0, 0, item.size * 0.6, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#fff'
    ctx.font = `${item.size * 0.5}px sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('$', 0, 0)
  }
  ctx.restore()
}

function drawStarShape(x, y, size) {
  ctx.beginPath()
  for (let i = 0; i < 5; i++) {
    const a = (i * 4 * Math.PI / 5) - Math.PI / 2
    ctx.lineTo(x + Math.cos(a) * size * 0.5, y + Math.sin(a) * size * 0.5)
    const b = a + 2 * Math.PI / 5
    ctx.lineTo(x + Math.cos(b) * size * 0.2, y + Math.sin(b) * size * 0.2)
  }
  ctx.closePath()
  ctx.fill()
}

function startGame() {
  score.value = 0
  combo = 1
  timeLeft.value = 60
  items = []
  particles = []
  player = { x: 0.5, targetX: 0.5, jumping: false, jumpY: 0, jumpVel: 0, grounded: true }
  comboText.value = 'x1'
  startOverlayVisible.value = false
  endOverlayVisible.value = false
  gameRunning = true
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) endGame()
  }, 1000)
  gameLoop()
}

function endGame() {
  gameRunning = false
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
  if (gameAnimId) { cancelAnimationFrame(gameAnimId); gameAnimId = null }
  finalMsg.value = score.value >= 500 ? '太厉害了！完美表现！' : score.value >= 200 ? '干得漂亮！继续加油！' : '还不错，再试一次吧！'
  endOverlayVisible.value = true
}

function startCalibration() {
  calibrating.value = true
  calibrateFrames = 0
  calibrateSamples = []
  calibrationData = null
  smoothedLm = null
  calibratePercent.value = 0
}

async function beginGame() {
  if (!localStream) {
    await startCameraFn()
  }
  startCalibration()
  const checkCalibration = setInterval(() => {
    if (!calibrating.value) {
      clearInterval(checkCalibration)
      startGame()
    }
  }, 100)
}

function handleResize() {
  if (canvasRef.value) {
    canvasRef.value.width = window.innerWidth
    canvasRef.value.height = window.innerHeight
  }
}

function handleKeydown(e) {
  if (!gameRunning) return
  if (e.key === 'ArrowLeft') player.targetX = Math.max(0.08, player.targetX - 0.04)
  if (e.key === 'ArrowRight') player.targetX = Math.min(0.92, player.targetX + 0.04)
  if ((e.key === ' ' || e.key === 'ArrowUp') && player.grounded) {
    player.jumping = true
    player.grounded = false
    player.jumpVel = -10
  }
}

onMounted(async () => {
  await nextTick()
  ctx = canvasRef.value.getContext('2d')
  camCtx = camPreviewRef.value.getContext('2d')
  canvasRef.value.width = window.innerWidth
  canvasRef.value.height = window.innerHeight
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
  initCameraSelector(cameraSelectorContainer.value, async () => {
    if (localStream) {
      localStream.getTracks().forEach(t => t.stop())
      localStream = await getSelectedStream()
      videoRef.value.srcObject = localStream
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  if (animId) { cancelAnimationFrame(animId); animId = null }
  if (gameAnimId) { cancelAnimationFrame(gameAnimId); gameAnimId = null }
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
  if (localStream) { localStream.getTracks().forEach(t => t.stop()); localStream = null }
  if (cameraStream.value) { cameraStream.value.getTracks().forEach(t => t.stop()); cameraStream.value = null }
  if (videoRef.value) videoRef.value.srcObject = null
  gameRunning = false
})
</script>

<style scoped>
.game-root {
  font-family: -apple-system, sans-serif;
  background: #000;
  color: #fff;
  overflow: hidden;
  height: 100vh;
  width: 100vw;
  position: relative;
}
.game-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
.back-link {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 20;
  color: #667eea;
  font-size: 14px;
  text-decoration: none;
  background: rgba(0,0,0,0.6);
  padding: 6px 14px;
  border-radius: 8px;
  backdrop-filter: blur(4px);
}
.back-link:hover {
  color: #8b9ff5;
}
.sidebar {
  position: fixed;
  top: 50px;
  right: 16px;
  z-index: 10;
  width: 220px;
}
.hud {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 30px;
}
.hud-item {
  background: rgba(0,0,0,0.6);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  backdrop-filter: blur(4px);
}
.hud-item .label {
  font-size: 11px;
  color: #888;
}
.hud-item .value {
  font-size: 24px;
  font-weight: 700;
}
.controls-hud {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}
.btn {
  padding: 10px 20px;
  background: rgba(30,30,30,0.8);
  border: 1px solid #444;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  backdrop-filter: blur(4px);
}
.btn:hover {
  background: rgba(50,50,50,0.8);
}
.btn.primary,
button.primary {
  background: rgba(26,115,232,0.8);
  border-color: #1a73e8;
}
.gesture-indicator {
  position: fixed;
  top: 16px;
  right: 250px;
  z-index: 10;
  background: rgba(0,0,0,0.6);
  padding: 12px 20px;
  border-radius: 12px;
  text-align: center;
  backdrop-filter: blur(4px);
}
.gesture-icon {
  font-size: 36px;
}
.gesture-text {
  font-size: 12px;
  color: #aaa;
  margin-top: 4px;
}
.game-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  z-index: 100;
}
.game-overlay h1 {
  font-size: 36px;
}
.game-overlay p {
  color: #888;
  max-width: 480px;
  text-align: center;
  line-height: 1.8;
  font-size: 15px;
}
.score-display {
  font-size: 48px;
  font-weight: 700;
  color: #4caf50;
}
.tutorial-gestures {
  display: flex;
  gap: 24px;
  margin: 16px 0;
}
.tutorial-item {
  text-align: center;
  background: rgba(255,255,255,0.05);
  padding: 16px 20px;
  border-radius: 12px;
  min-width: 120px;
}
.tutorial-item .icon {
  font-size: 40px;
  display: block;
  margin-bottom: 8px;
}
.tutorial-item .desc {
  font-size: 12px;
  color: #aaa;
}
.tutorial-item .label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}
.play-btn {
  font-size: 18px;
  padding: 12px 32px;
  cursor: pointer;
  border: 1px solid #1a73e8;
  border-radius: 8px;
  color: #fff;
}
.mini-cam {
  position: fixed;
  bottom: 60px;
  right: 16px;
  width: 200px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #333;
  z-index: 10;
}
.mini-cam canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.calibrate-bar {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0,0,0,0.85);
  padding: 32px 48px;
  border-radius: 16px;
  text-align: center;
  z-index: 200;
}
.calibrate-bar h2 {
  margin-bottom: 12px;
}
.calibrate-bar p {
  color: #aaa;
  margin-bottom: 16px;
}
.progress-bar {
  width: 300px;
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
}
.progress-bar .fill {
  height: 100%;
  background: #4caf50;
  transition: width 0.1s;
}
.hint-bar {
  position: fixed;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.7);
  padding: 8px 24px;
  border-radius: 20px;
  font-size: 13px;
  color: #aaa;
  z-index: 10;
}
</style>
