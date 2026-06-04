<template>
  <div class="game-page">
    <header class="top-bar">
      <div class="top-left">
        <button class="back-btn" @click="goBack">← 返回</button>
        <span class="world-badge">{{ worldLabel }}</span>
      </div>
      <div class="top-right">
        <span class="stage-indicator">{{ stageName }}</span>
      </div>
    </header>

    <div v-if="!started" class="loading-screen">
      <div class="loading-spinner"></div>
      <p>命运正在编织…</p>
    </div>

    <div v-else-if="ending" class="ending-screen">
      <div class="ending-card">
        <div class="ending-score">
          <span class="score-num">{{ ending.score }}</span>
          <span class="score-label">人生评分</span>
        </div>
        <h2 class="ending-title">{{ ending.title }}</h2>
        <div class="ending-tags">
          <span v-for="tag in ending.tags" :key="tag" class="ending-tag">{{ tag }}</span>
        </div>
        <div class="ending-text">
          <TypewriterText :text="ending.ending" :speed="typewriterSpeed" @complete="onEndingComplete" />
        </div>
        <div class="ending-actions">
          <button class="restart-btn" @click="restart">🔄 重开人生</button>
          <button class="change-btn" @click="goHome">🌍 换个世界观</button>
        </div>
      </div>

      <div class="ending-timeline">
        <h4>完整人生轨迹</h4>
        <div class="full-timeline">
          <div v-for="(item, i) in history" :key="i" class="ft-item">
            <div class="ft-dot"></div>
            <div class="ft-line" v-if="i < history.length - 1"></div>
            <div class="ft-content">
              <span class="ft-stage">{{ item.stage_name }}</span>
              <span class="ft-tag">{{ item.event_tag }}</span>
              <span v-if="item.choice_text" class="ft-choice">→ {{ item.choice_text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="game-layout">
      <aside class="sidebar">
        <div class="speed-control">
          <div class="speed-header">
            <label>打字速度</label>
            <span class="speed-value">{{ charsPerSecond }} 字/秒</span>
          </div>
          <input 
            type="range" 
            v-model="typewriterSpeed" 
            min="10" 
            max="200" 
            step="5"
          />
          <div class="speed-labels">
            <span>快</span>
            <span>中</span>
            <span>慢</span>
          </div>
        </div>
        <AttributePanel :attributes="attributes" :background="background" />
        <Timeline :items="history" :current-stage-name="stageName" />
      </aside>

      <main class="main-area">
        <div class="story-card">
          <div class="story-header">
            <span class="story-stage">{{ stageName }}</span>
            <span v-if="eventTag" class="story-tag">{{ eventTag }}</span>
          </div>
          <div class="story-body">
            <TypewriterText
              ref="typewriterRef"
              :text="story"
              :speed="typewriterSpeed"
              @complete="onStoryComplete"
            />
          </div>
        </div>

        <div class="choice-area">
          <ChoiceButtons
            :options="options"
            :unlocked="choicesUnlocked"
            @choose="onChoose"
          />
        </div>

        <div v-if="isLoading" class="loading-inline">
          <div class="loading-spinner small"></div>
          <span>命运正在改写…</span>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLifeSimulator } from '../../composables/useLifeSimulator.js'
import TypewriterText from './TypewriterText.vue'
import AttributePanel from './AttributePanel.vue'
import Timeline from './Timeline.vue'
import ChoiceButtons from './ChoiceButtons.vue'

const route = useRoute()
const router = useRouter()
const {
  worldType, attributes, background, story, options,
  stage, stageName, eventTag, isActive, isLoading,
  history, ending, startGame, makeChoice, reset,
} = useLifeSimulator()

const started = ref(false)
const choicesUnlocked = ref(false)
const typewriterRef = ref(null)
const typewriterSpeed = ref(50)
const endingComplete = ref(false)

const charsPerSecond = computed(() => {
  return Math.round(1000 / typewriterSpeed.value)
})

const worldLabels = { modern: '现代都市', ancient: '古代江湖', future: '未来科幻' }
const worldLabel = computed(() => worldLabels[worldType.value] || '')

async function init() {
  const type = route.query.world || 'modern'
  try {
    await startGame(type)
    started.value = true
  } catch (e) {
    alert('启动游戏失败：' + e.message)
    router.push('/life')
  }
}

function onStoryComplete() {
  choicesUnlocked.value = true
}

function onEndingComplete() {
  endingComplete.value = true
}

async function onChoose(choiceId) {
  choicesUnlocked.value = false
  await makeChoice(choiceId)
}

function restart() {
  reset()
  started.value = false
  endingComplete.value = false
  typewriterSpeed.value = 50
  init()
}

function goBack() {
  if (isActive.value) {
    if (confirm('确定要退出当前人生吗？进度将不会保存。')) {
      reset()
      router.push('/life')
    }
  } else {
    reset()
    router.push('/life')
  }
}

function goHome() {
  reset()
  router.push('/life')
}

onMounted(init)
</script>

<style scoped>
.game-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 32px;
  background: rgba(250, 249, 247, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #e8e8e8;
}
.top-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.back-btn {
  font-size: 14px;
  color: #888;
  background: none;
  padding: 4px 0;
  transition: color 0.15s;
}
.back-btn:hover { color: #7c3aed; }
.world-badge {
  font-size: 12px;
  color: #7c3aed;
  background: #f5f3ff;
  padding: 3px 10px;
  border-radius: 20px;
}
.stage-indicator {
  font-size: 13px;
  color: #888;
}

.loading-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}
.loading-screen p {
  font-size: 14px;
  color: #999;
}
.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid #e8e8e8;
  border-top-color: #7c3aed;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.loading-spinner.small {
  width: 18px;
  height: 18px;
  border-width: 2px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.ending-screen {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 32px 80px;
  width: 100%;
}
.ending-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  margin-bottom: 32px;
}
.ending-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
}
.score-num {
  font-size: 56px;
  font-weight: 700;
  color: #7c3aed;
  line-height: 1;
}
.score-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}
.ending-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 12px;
}
.ending-tags {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 24px;
}
.ending-tag {
  font-size: 12px;
  color: #7c3aed;
  background: #f5f3ff;
  padding: 4px 12px;
  border-radius: 20px;
}
.ending-text {
  text-align: left;
  max-width: 560px;
  margin: 0 auto 24px;
  padding: 20px;
  background: #faf9f7;
  border-radius: 12px;
}
.ending-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.restart-btn, .change-btn {
  font-size: 14px;
  padding: 10px 24px;
  border-radius: 10px;
  transition: all 0.15s;
}
.restart-btn {
  background: #7c3aed;
  color: white;
}
.restart-btn:hover { background: #6d28d9; }
.change-btn {
  background: #f5f5f5;
  color: #666;
}
.change-btn:hover { background: #e8e8e8; }

.ending-timeline {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 16px;
  padding: 32px;
}
.ending-timeline h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 20px;
}
.full-timeline {
  display: flex;
  flex-direction: column;
  max-height: 400px;
  overflow-y: auto;
}
.ft-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
  padding-bottom: 20px;
}
.ft-item:last-child { padding-bottom: 0; }
.ft-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #d1d5db;
  flex-shrink: 0;
  margin-top: 4px;
  z-index: 1;
}
.ft-item:last-child .ft-dot {
  background: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
}
.ft-line {
  position: absolute;
  left: 4px;
  top: 14px;
  bottom: 0;
  width: 1px;
  background: #e8e8e8;
}
.ft-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ft-stage {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}
.ft-tag {
  font-size: 12px;
  color: #999;
}
.ft-choice {
  font-size: 12px;
  color: #7c3aed;
}

.game-layout {
  display: flex;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 32px 80px;
  width: 100%;
}
.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.speed-control {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.speed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.speed-control label {
  font-size: 12px;
  color: #888;
}
.speed-value {
  font-size: 14px;
  font-weight: 600;
  color: #7c3aed;
}
.speed-control input[type="range"] {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  background: linear-gradient(to right, #e8e8e8 0%, #7c3aed 100%);
  border-radius: 3px;
  outline: none;
}
.speed-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: #ffffff;
  border: 2px solid #7c3aed;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(124, 58, 237, 0.2);
}
.speed-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #aaa;
}

.main-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.story-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
}
.story-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  border-bottom: 1px solid #f0f0f0;
}
.story-stage {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}
.story-tag {
  font-size: 11px;
  color: #7c3aed;
  background: #f5f3ff;
  padding: 2px 8px;
  border-radius: 10px;
}
.story-body {
  padding: 24px;
  min-height: 200px;
}

.choice-area {
  padding: 0;
}

.loading-inline {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  padding: 16px;
  font-size: 13px;
  color: #999;
}

@media (max-width: 900px) {
  .game-layout {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
  }
  .sidebar > * {
    flex: 1;
    min-width: 240px;
  }
}
</style>
