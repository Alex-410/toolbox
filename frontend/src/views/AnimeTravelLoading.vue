<template>
  <div class="loading-page">
    <button class="back-btn" @click="goBack">
      <span class="back-icon">&#8592;</span>
      <span>返回</span>
    </button>

    <div
      class="terminal"
      :style="{
        left: pos.x + 'px',
        top: pos.y + 'px',
        width: size.w + 'px',
        height: size.h + 'px',
      }"
    >
      <div class="terminal-header" @mousedown="onDragStart">
        <div class="terminal-dots">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
        </div>
        <span class="terminal-title">Terminal</span>
      </div>
      <div class="terminal-body" ref="termBody" @click="focusInput">
        <div v-for="(line, i) in lines" :key="i" :class="['term-line', line.type]">
          <template v-if="line.type === 'input'">
            <span class="prompt">{{ line.cwd }}&gt;</span>
            <span class="cmd">{{ line.text }}</span>
          </template>
          <template v-else>
            <pre class="output" v-html="renderOutput(line.text)"></pre>
          </template>
        </div>
        <div class="input-line">
          <span class="prompt">{{ cwd }}&gt;</span>
          <input
            v-if="!busy"
            ref="termInput"
            v-model="input"
            @keydown="onKeydown"
            class="term-input"
            spellcheck="false"
            autofocus
          />
          <span v-else class="busy-text">执行中...</span>
        </div>
      </div>
      <div class="resize-handle n" @mousedown="(e) => onResizeStart(e, 'n')"></div>
      <div class="resize-handle s" @mousedown="(e) => onResizeStart(e, 's')"></div>
      <div class="resize-handle w" @mousedown="(e) => onResizeStart(e, 'w')"></div>
      <div class="resize-handle e" @mousedown="(e) => onResizeStart(e, 'e')"></div>
      <div class="resize-handle nw" @mousedown="(e) => onResizeStart(e, 'nw')"></div>
      <div class="resize-handle ne" @mousedown="(e) => onResizeStart(e, 'ne')"></div>
      <div class="resize-handle sw" @mousedown="(e) => onResizeStart(e, 'sw')"></div>
      <div class="resize-handle se" @mousedown="(e) => onResizeStart(e, 'se')"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const cwd = ref('c:\\Users\\hp\\Desktop\\claude\\anime-travel')
const input = ref('')
const lines = ref([])
const history = ref([])
const historyIndex = ref(-1)
const termBody = ref(null)
const termInput = ref(null)
const busy = ref(false)

const pos = reactive({ x: 0, y: 0 })
const size = reactive({ w: 0, h: 0 })

let dragState = null
let resizeState = null

function goBack() {
  router.back()
}

function focusInput() {
  termInput.value?.focus()
}

function calcDefaultPos() {
  size.w = Math.min(900, window.innerWidth * 0.8)
  size.h = Math.min(600, window.innerHeight * 0.7)
  pos.x = Math.max(0, (window.innerWidth - size.w) / 2)
  pos.y = Math.max(40, (window.innerHeight - size.h) / 2)
}

function onDragStart(e) {
  if (e.target.classList.contains('dot')) return
  e.preventDefault()
  dragState = { startX: e.clientX - pos.x, startY: e.clientY - pos.y }
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
}

function onDragMove(e) {
  if (!dragState) return
  pos.x = Math.max(0, Math.min(window.innerWidth - size.w, e.clientX - dragState.startX))
  pos.y = Math.max(0, Math.min(window.innerHeight - size.h, e.clientY - dragState.startY))
}

function onDragEnd() {
  dragState = null
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

function onResizeStart(e, dir) {
  e.preventDefault()
  e.stopPropagation()
  resizeState = { startX: e.clientX, startY: e.clientY, startW: size.w, startH: size.h, startPosX: pos.x, startPosY: pos.y, dir }
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}

function onResizeMove(e) {
  if (!resizeState) return
  const dx = e.clientX - resizeState.startX
  const dy = e.clientY - resizeState.startY
  const d = resizeState.dir

  if (d.includes('e')) {
    size.w = Math.max(400, Math.min(window.innerWidth - pos.x, resizeState.startW + dx))
  }
  if (d.includes('w')) {
    const newW = Math.max(400, resizeState.startW - dx)
    const newX = resizeState.startPosX + resizeState.startW - newW
    if (newX >= 0) { size.w = newW; pos.x = newX }
  }
  if (d.includes('s')) {
    size.h = Math.max(250, Math.min(window.innerHeight - pos.y, resizeState.startH + dy))
  }
  if (d.includes('n')) {
    const newH = Math.max(250, resizeState.startH - dy)
    const newY = resizeState.startPosY + resizeState.startH - newH
    if (newY >= 0) { size.h = newH; pos.y = newY }
  }
}

function onResizeEnd() {
  resizeState = null
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}

const URL_RE = /(https?:\/\/[^\s<>"')\]]+)/g
const ESC_MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ESC_MAP[c])
}

function renderOutput(text) {
  return escapeHtml(text).replace(URL_RE, '<a href="$1" target="_self" class="term-link">$1</a>')
}

function scrollToBottom() {
  nextTick(() => {
    if (termBody.value) {
      termBody.value.scrollTop = termBody.value.scrollHeight
    }
  })
}

function addLine(text, type = 'output') {
  lines.value.push({ text, type })
  scrollToBottom()
}

async function execute(command) {
  const cmd = command.trim()
  if (!cmd || busy.value) return

  lines.value.push({ type: 'input', text: cmd, cwd: cwd.value })
  history.value.push(cmd)
  historyIndex.value = -1

  if (cmd === 'clear' || cmd === 'cls') {
    lines.value = []
    return
  }

  busy.value = true

  if (cmd.startsWith('cd ') || cmd === 'cd') {
    const target = cmd === 'cd' ? '' : cmd.slice(3).trim()
    try {
      const res = await fetch('/api/anime-travel/exec/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: `cd /d "${target}" && cd`, cwd: cwd.value }),
      })
      const data = await res.json()
      if (data.returncode === 0 && data.stdout) {
        cwd.value = data.stdout.trim().replace(/\n/g, '')
      } else if (data.stderr) {
        addLine(data.stderr, 'stderr')
      }
    } catch (e) {
      addLine('Error: ' + e.message, 'stderr')
    }
    busy.value = false
    return
  }

  try {
    const res = await fetch('/api/anime-travel/exec/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd, cwd: cwd.value }),
    })
    const data = await res.json()
    if (data.cwd) cwd.value = data.cwd
    if (data.stdout) addLine(data.stdout, 'stdout')
    if (data.stderr) addLine(data.stderr, 'stderr')
    if (data.running) {
      addLine(`[进程仍在运行中 PID:${data.pid}]`, 'running')
    }
  } catch (e) {
    addLine('Error: ' + e.message, 'stderr')
  }

  busy.value = false
}

function onKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    const cmd = input.value
    input.value = ''
    execute(cmd)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (history.value.length === 0) return
    if (historyIndex.value === -1) {
      historyIndex.value = history.value.length - 1
    } else if (historyIndex.value > 0) {
      historyIndex.value--
    }
    input.value = history.value[historyIndex.value]
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (historyIndex.value === -1) return
    if (historyIndex.value < history.value.length - 1) {
      historyIndex.value++
      input.value = history.value[historyIndex.value]
    } else {
      historyIndex.value = -1
      input.value = ''
    }
  }
}

watch(busy, (val) => {
  if (!val) {
    nextTick(() => termInput.value?.focus())
  }
})

onMounted(() => {
  calcDefaultPos()
  addLine('欢迎使用终端。输入命令开始操作。', 'info')
  addLine(`当前路径: ${cwd.value}`, 'info')
  addLine('提示: cd c:\\path 切换目录 | clear 清屏 | npm run dev 启动服务', 'info')
  termInput.value?.focus()
})
</script>

<style scoped>
.loading-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #1a1a2e;
  overflow: hidden;
}

.loading-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('https://acg.yaohud.cn/dm/adaptive.php');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.75;
  z-index: 0;
}

.back-btn {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  backdrop-filter: blur(8px);
  transition: background 0.2s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.back-icon {
  font-size: 18px;
}

.terminal {
  position: absolute;
  z-index: 10;
  background: rgba(30, 30, 46, 0.5);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
}

.terminal-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  gap: 10px;
  cursor: grab;
  user-select: none;
}

.terminal-header:active {
  cursor: grabbing;
}

.terminal-dots {
  display: flex;
  gap: 7px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red { background: #ff5f57; }
.dot.yellow { background: #febc2e; }
.dot.green { background: #28c840; }

.terminal-title {
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  font-family: 'Consolas', 'Courier New', monospace;
}

.terminal-body {
  flex: 1;
  padding: 14px;
  overflow-y: auto;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
}

.terminal-body::-webkit-scrollbar {
  width: 6px;
}

.terminal-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

.term-line {
  margin-bottom: 2px;
  white-space: pre-wrap;
  word-break: break-all;
}

.term-line.input .prompt {
  color: #67c23a;
  margin-right: 8px;
}

.term-line.input .cmd {
  color: #fff;
}

.term-line.stdout {
  color: #d4d4d4;
}

.term-line.stderr {
  color: #f56c6c;
}

.term-line.info {
  color: #888;
  font-style: italic;
}

.term-line.running {
  color: #e6a23c;
  font-style: italic;
}

.output {
  margin: 0;
  font-family: inherit;
  font-size: inherit;
  white-space: pre-wrap;
  word-break: break-all;
}

.output :deep(.term-link) {
  color: #58a6ff;
  text-decoration: underline;
  cursor: pointer;
}

.output :deep(.term-link:hover) {
  color: #79c0ff;
}

.input-line {
  display: flex;
  align-items: center;
}

.prompt {
  color: #67c23a;
  margin-right: 8px;
  flex-shrink: 0;
  user-select: none;
}

.term-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 14px;
  caret-color: #67c23a;
}

.busy-text {
  color: #e6a23c;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.resize-handle {
  position: absolute;
  z-index: 20;
}

.resize-handle.n {
  top: -3px; left: 8px; right: 8px; height: 6px;
  cursor: ns-resize;
}

.resize-handle.s {
  bottom: -3px; left: 8px; right: 8px; height: 6px;
  cursor: ns-resize;
}

.resize-handle.w {
  left: -3px; top: 8px; bottom: 8px; width: 6px;
  cursor: ew-resize;
}

.resize-handle.e {
  right: -3px; top: 8px; bottom: 8px; width: 6px;
  cursor: ew-resize;
}

.resize-handle.nw {
  top: -4px; left: -4px; width: 12px; height: 12px;
  cursor: nwse-resize;
}

.resize-handle.ne {
  top: -4px; right: -4px; width: 12px; height: 12px;
  cursor: nesw-resize;
}

.resize-handle.sw {
  bottom: -4px; left: -4px; width: 12px; height: 12px;
  cursor: nesw-resize;
}

.resize-handle.se {
  bottom: -4px; right: -4px; width: 12px; height: 12px;
  cursor: nwse-resize;
}
</style>
