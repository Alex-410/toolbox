<template>
  <div class="ai-itinerary">
    <div class="ai-header" @click="toggle">
      <div class="ai-header-left">
        <el-icon><MagicStick /></el-icon>
        <span>AI 智能行程规划</span>
        <el-tag v-if="aiItinerary" size="small" type="success">已完成</el-tag>
      </div>
      <el-icon class="ai-arrow" :class="{ rotated: expanded }">
        <ArrowDown />
      </el-icon>
    </div>

    <div v-if="expanded" class="ai-content">
      <div v-if="!aiItinerary" class="ai-empty">
        <p>点击下方按钮生成 AI 智能行程规划</p>
        <ul class="ai-features">
          <li>📍 智能排序，每天 3-4 个地点</li>
          <li>🚇 交通衔接建议</li>
          <li>🍜 餐饮休息推荐</li>
          <li>📸 打卡拍照建议</li>
        </ul>
        <el-button
          type="primary"
          @click="handleGenerate"
          :loading="aiLoading"
          :disabled="librarySelected.length === 0"
        >
          <el-icon v-if="!aiLoading"><MagicStick /></el-icon>
          生成 AI 行程
        </el-button>
        <div v-if="ollamaStatus === false" class="ai-warning">
          <el-icon><WarningFilled /></el-icon>
          Ollama 服务未启动，请确保已运行
        </div>
      </div>

      <div v-else class="ai-result">
        <div class="ai-result-header">
          <el-button text size="small" @click="handleRegenerate" :loading="aiLoading">
            <el-icon><Refresh /></el-icon>
            重新生成
          </el-button>
          <el-button text size="small" @click="handleCopy">
            <el-icon><DocumentCopy /></el-icon>
            复制
          </el-button>
        </div>
        <div class="ai-result-content markdown-body" v-html="formattedItinerary"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { MagicStick, ArrowDown, WarningFilled, Refresh, DocumentCopy } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'
import { storeToRefs } from 'pinia'
import { generateItineraryWithOllama, checkOllamaStatus } from '../utils/ollama'
import { ElMessage } from 'element-plus'

const store = useAppStore()
const { librarySelected, libraryItinerary, libraryDays } = storeToRefs(store)

const expanded = ref(false)
const aiItinerary = ref('')
const aiLoading = ref(false)
const ollamaStatus = ref(null)

const formattedItinerary = computed(() => {
  if (!aiItinerary.value) return ''
  return aiItinerary.value
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
})

function toggle() {
  expanded.value = !expanded.value
}

async function handleGenerate() {
  if (librarySelected.value.length === 0) {
    ElMessage.warning('请先选择要规划的地标')
    return
  }

  aiLoading.value = true

  try {
    const points = librarySelected.value.map(p => ({
      name: p.name,
      anime: p.bangumiName || '',
      ep: p.ep || '',
      lat: p.geo ? p.geo[0] : 0,
      lon: p.geo ? p.geo[1] : 0
    }))

    const animeNames = [...new Set(points.map(p => p.anime).filter(Boolean))]
    if (animeNames.length === 0) animeNames = ['动漫']

    const routeInfo = {
      totalDistance: libraryItinerary.value.reduce((sum, day) => sum + (day.distance || 0), 0),
      totalDuration: 0
    }

    const result = await generateItineraryWithOllama(
      animeNames,
      libraryDays.value,
      points,
      routeInfo
    )

    aiItinerary.value = result
    ElMessage.success('AI 行程规划生成成功！')
  } catch (error) {
    console.error('AI 行程生成失败:', error)
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    aiLoading.value = false
  }
}

function handleRegenerate() {
  handleGenerate()
}

function handleCopy() {
  if (aiItinerary.value) {
    navigator.clipboard.writeText(aiItinerary.value)
    ElMessage.success('已复制到剪贴板')
  }
}

onMounted(async () => {
  const status = await checkOllamaStatus()
  ollamaStatus.value = status.available
})
</script>

<style scoped>
.ai-itinerary {
  border-top: 1px solid var(--border-color);
  background: var(--sidebar-bg);
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.ai-header:hover {
  background-color: rgba(64, 158, 255, 0.06);
}

.ai-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--text-color);
}

.ai-arrow {
  transition: transform 0.18s ease;
}

.ai-arrow.rotated {
  transform: rotate(180deg);
}

.ai-content {
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
}

.ai-empty {
  text-align: center;
}

.ai-empty p {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 12px;
}

.ai-features {
  list-style: none;
  padding: 0;
  margin: 0 0 16px 0;
  text-align: left;
  font-size: 12px;
  color: var(--text-secondary);
}

.ai-features li {
  padding: 4px 0;
}

.ai-warning {
  margin-top: 12px;
  padding: 8px 12px;
  background: rgba(230, 162, 60, 0.1);
  border-radius: 6px;
  color: #E6A23C;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ai-result {
  max-height: 400px;
  overflow-y: auto;
}

.ai-result-header {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 12px;
}

.ai-result-content {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-color);
}

.ai-result-content :deep(h1) {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--text-color);
}

.ai-result-content :deep(h2) {
  font-size: 15px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: var(--text-color);
}

.ai-result-content :deep(h3) {
  font-size: 14px;
  font-weight: 500;
  margin: 12px 0 6px 0;
}

.ai-result-content :deep(li) {
  margin: 4px 0;
  padding-left: 8px;
}

.markdown-body {
  white-space: pre-wrap;
}
</style>
