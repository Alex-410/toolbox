<template>
  <div class="coordinate-library" :class="{ expanded }">
    <div class="lib-header" @click="toggle">
      <div class="lib-header-left">
        <h3>坐标库</h3>
        <el-tag v-if="coordinateLibrary.length > 0" size="small" effect="dark">
          {{ librarySelected.length }}/{{ coordinateLibrary.length }}
        </el-tag>
      </div>
      <el-icon v-if="coordinateLibrary.length > 0" class="lib-arrow" :class="{ rotated: expanded }">
        <ArrowDown />
      </el-icon>
    </div>

    <div v-if="coordinateLibrary.length === 0" class="lib-empty">
      <el-icon :size="20" color="var(--text-secondary)"><Star /></el-icon>
      <span>点击地图地标卡片上的 ☆ 收藏坐标</span>
    </div>

    <template v-else>
      <div class="lib-toolbar">
        <el-checkbox
          :model-value="coordinateLibrary.length > 0 && coordinateLibrary.every(e => e.checked)"
          :indeterminate="librarySelected.length > 0 && librarySelected.length < coordinateLibrary.length"
          @change="handleCheckAll"
          @click.stop
        >
          全选
        </el-checkbox>
        <div class="lib-toolbar-actions">
          <el-button text size="small" @click.stop="store.libraryCheckAll()">全选</el-button>
          <el-button text size="small" @click.stop="store.libraryUncheckAll()">清空</el-button>
        </div>
      </div>

      <div class="lib-list scrollbar-wrapper">
        <div
          v-for="entry in coordinateLibrary"
          :key="entry.id"
          class="lib-item"
          :class="{ unchecked: !entry.checked }"
        >
          <el-checkbox
            :model-value="entry.checked"
            @change="store.toggleLibraryItem(entry.id)"
            @click.stop
          />
          <div class="lib-thumb" v-if="entry.image">
            <img :src="getThumbUrl(entry.image)" :alt="entry.name" loading="lazy" />
          </div>
          <div class="lib-thumb placeholder" v-else>
            <el-icon :size="14"><Star /></el-icon>
          </div>
          <div class="lib-info">
            <div class="lib-name">{{ entry.name }}</div>
            <div class="lib-source" v-if="entry.bangumiName">{{ entry.bangumiName }}</div>
          </div>
          <el-button
            text
            size="small"
            class="lib-remove-btn"
            @click.stop="store.removeFromLibrary(entry.id)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <div class="lib-controls">
        <div class="lib-mode-row">
          <el-select v-model="planMode" size="small" style="width: 100px">
            <el-option label="智能规划" value="intelligent" />
            <el-option label="按集数" value="episode" />
            <el-option label="按时间" value="time" />
          </el-select>
          <el-select v-model="routeType" size="small" style="width: 80px">
            <el-option label="驾车" value="driving" />
            <el-option label="步行" value="walking" />
            <el-option label="骑行" value="cycling" />
          </el-select>
        </div>
        <div class="lib-days-row">
          <span class="lib-label">天数</span>
          <el-input-number
            v-model="libraryDays"
            :min="1"
            :max="7"
            size="small"
            :disabled="librarySelected.length === 0"
          />
        </div>
        <el-button
          type="primary"
          size="small"
          @click="handleGenerate"
          :loading="loading"
          :disabled="librarySelected.length === 0"
        >
          生成路线
        </el-button>
      </div>

      <div v-if="libraryItinerary.length > 0" class="lib-itinerary scrollbar-wrapper">
        <div v-for="day in libraryItinerary" :key="day.day" class="lib-day">
          <div class="lib-day-header">
            <span class="lib-day-badge" :style="{ backgroundColor: dayColors[(day.day - 1) % dayColors.length] }">
              第{{ day.day }}天
            </span>
            <span class="lib-day-stats">{{ day.pointCount }} 地点 · {{ day.distance }}km</span>
          </div>
          <div
            v-for="(pt, idx) in day.points"
            :key="pt.id"
            class="lib-day-point"
            @click="store.selectPoint(pt.id)"
          >
            <span class="lib-pt-num" :style="{ backgroundColor: dayColors[(day.day - 1) % dayColors.length] }">{{ idx + 1 }}</span>
            <span class="lib-pt-name">{{ pt.name }}</span>
          </div>
        </div>

        <div v-if="aiItinerary" class="ai-result">
          <div class="ai-result-header">
            <span class="ai-result-title">🤖 AI 行程规划</span>
            <el-button text size="small" @click="copyAiItinerary">
              复制
            </el-button>
          </div>
          <pre class="ai-result-content">{{ formattedAiItinerary }}</pre>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Star, Close, ArrowDown } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'
import { storeToRefs } from 'pinia'
import { PLAN_MODE } from '../utils/routePlanner'

const store = useAppStore()
const { coordinateLibrary, librarySelected, libraryItinerary, loading, routeType, libraryDays: storeLibraryDays, aiItinerary } = storeToRefs(store)

const expanded = ref(false)
const dayColors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#b37feb', '#36cfc9']

const formattedAiItinerary = computed(function() {
  if (!aiItinerary.value) return ''
  return aiItinerary.value
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^[-*+]\s+/gm, '')
    .replace(/^\d+\.\s+/gm, '')
    .replace(/^---\s*$/gm, '')
    .replace(/\|[^|]*\|/g, function(match) {
      return match.replace(/[|:]/g, ' ').trim()
    })
})

const libraryDays = storeLibraryDays
const planMode = ref(PLAN_MODE.INTELLIGENT)

function toggle() {
  if (coordinateLibrary.value.length > 0) {
    expanded.value = !expanded.value
  }
}

function handleCheckAll(val) {
  if (val) store.libraryCheckAll()
  else store.libraryUncheckAll()
}

async function handleGenerate() {
  store.generateLibraryItinerary({
    mode: planMode.value,
    routeType: routeType.value
  })
}

function copyAiItinerary() {
  if (aiItinerary.value) {
    navigator.clipboard.writeText(aiItinerary.value)
  }
}

function getThumbUrl(imageUrl) {
  if (!imageUrl) return ''
  if (imageUrl.includes('?')) return imageUrl
  return imageUrl + '?plan=h160'
}
</script>

<style scoped>
.coordinate-library {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--border-color);
  max-height: 45vh;
  min-height: 0;
  flex-shrink: 0;
  transition: max-height 0.18s ease;
  overflow: hidden;
}

.coordinate-library.expanded {
  max-height: 85vh;
}

.lib-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.15s;
}

.lib-header:hover {
  background-color: rgba(64, 158, 255, 0.06);
}

.lib-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lib-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.lib-arrow {
  font-size: 14px;
  color: var(--text-secondary);
  transition: transform 0.18s ease;
}

.lib-arrow.rotated {
  transform: rotate(180deg);
}

.lib-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 20px;
  font-size: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.lib-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.lib-toolbar-actions {
  display: flex;
  gap: 2px;
}

.lib-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 12px;
  min-height: 0;
  max-height: 120px;
  transition: max-height 0.18s ease;
}

.expanded .lib-list {
  max-height: none;
  flex: 1;
}

.lib-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  transition: background-color 0.2s, opacity 0.2s;
  margin-bottom: 2px;
}

.lib-item:hover {
  background-color: rgba(64, 158, 255, 0.08);
}

.lib-item.unchecked {
  opacity: 0.45;
}

.lib-thumb {
  flex-shrink: 0;
  width: 40px;
  height: 28px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--card-bg);
}

.lib-thumb.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}

.lib-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.lib-info {
  flex: 1;
  min-width: 0;
}

.lib-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

.lib-source {
  font-size: 10px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 1px;
}

.lib-remove-btn {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
  padding: 2px !important;
  height: auto !important;
}

.lib-item:hover .lib-remove-btn {
  opacity: 0.7;
}

.lib-remove-btn:hover {
  opacity: 1 !important;
  color: #F56C6C !important;
}

.lib-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  border-top: 1px solid var(--border-color);
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.lib-mode-row {
  display: flex;
  gap: 6px;
}

.lib-days-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lib-label {
  font-size: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.lib-itinerary {
  max-height: 160px;
  overflow-y: auto;
  padding: 6px 12px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.lib-day {
  margin-bottom: 8px;
}

.lib-day:last-child {
  margin-bottom: 0;
}

.lib-day-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  margin-bottom: 4px;
}

.lib-day-badge {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  color: white;
}

.lib-day-stats {
  font-size: 11px;
  color: var(--text-secondary);
}

.lib-day-point {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.lib-day-point:hover {
  background-color: rgba(64, 158, 255, 0.08);
}

.lib-pt-num {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: white;
}

.lib-pt-name {
  flex: 1;
  font-size: 12px;
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lib-itinerary {
  border-top: 1px solid var(--border-color);
  max-height: 300px;
  overflow-y: auto;
}

.ai-result {
  border-top: 1px solid var(--border-color);
  padding: 12px;
  background: rgba(64, 158, 255, 0.03);
}

.ai-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ai-result-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-color);
}

.ai-result-content {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-color);
  white-space: pre-wrap;
  word-wrap: break-word;
  background: var(--sidebar-bg);
  padding: 10px;
  border-radius: 6px;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
}
</style>
