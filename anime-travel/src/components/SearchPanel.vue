<template>
  <div class="search-panel">
    <div class="search-header">
      <h2 class="app-title">
        <a class="back-home" href="http://localhost:5173/">
          <span class="back-arrow">
            <el-icon :size="14"><Back /></el-icon>
          </span>
        </a>
        动漫巡礼
      </h2>
      <p class="app-subtitle">搜索作品，规划你的圣地巡礼路线</p>
    </div>

    <div class="search-input-group">
      <el-input
        v-model="searchText"
        placeholder="作品名称 或 Bangumi ID"
        size="large"
        @keyup.enter="handleSearch"
        @input="handleInput"
        :disabled="loading"
        clearable
        @clear="handleClear"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <span>搜索结果 ({{ searchResults.length }})</span>
        <el-button text size="small" @click="store.clearSearchResults()">关闭</el-button>
      </div>
      <div class="results-list scrollbar-wrapper">
        <div
          v-for="item in searchResults"
          :key="item.id"
          class="result-item"
          @click="handleSelectResult(item)"
        >
          <div class="result-cover" v-if="item.image">
            <img :src="item.image" :alt="item.name_cn || item.name" loading="lazy" />
          </div>
          <div class="result-cover placeholder" v-else>
            <el-icon :size="20"><Picture /></el-icon>
          </div>
          <div class="result-info">
            <div class="result-name">{{ item.name_cn || item.name }}</div>
            <div v-if="item.name_cn && item.name !== item.name_cn" class="result-original">{{ item.name }}</div>
            <div class="result-meta">
              <span v-if="item.air_date">放送: {{ item.air_date }}</span>
              <span class="result-id">ID: {{ item.id }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <el-alert :title="error" type="error" show-icon :closable="false" />
    </div>

    <div v-if="bangumi" class="bangumi-info">
      <div class="bangumi-cover-wrapper">
        <img :src="bangumi.cover" :alt="bangumi.cn" class="bangumi-cover" />
      </div>
      <div class="bangumi-details">
        <h3 class="bangumi-title">{{ bangumi.cn || bangumi.title }}</h3>
        <p v-if="bangumi.title !== bangumi.cn" class="bangumi-original-title">{{ bangumi.title }}</p>
        <div class="bangumi-meta">
          <el-tag v-if="bangumi.city" size="small" effect="dark">{{ bangumi.city }}</el-tag>
          <el-tag size="small" effect="plain">{{ points.length }} 个地标</el-tag>
          <el-tag size="small" type="info">ID: {{ bangumi.id }}</el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, Picture, Back } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'
import { storeToRefs } from 'pinia'

const store = useAppStore()
const { bangumi, points, loading, error, searchResults } = storeToRefs(store)

const searchText = ref('')
let searchTimer = null

function handleInput(val) {
  if (searchTimer) clearTimeout(searchTimer)
  if (!val || !val.trim()) {
    store.clearSearchResults()
    return
  }
  if (/^\d+$/.test(val.trim())) {
    store.clearSearchResults()
    return
  }
  searchTimer = setTimeout(() => {
    store.searchByKey(val)
  }, 500)
}

async function handleSearch() {
  if (!searchText.value) return
  const text = searchText.value.trim()
  if (/^\d+$/.test(text)) {
    store.clearSearchResults()
    await store.searchBangumi(text)
  } else {
    await store.searchByKey(text)
  }
}

async function handleSelectResult(item) {
  searchText.value = String(item.id)
  store.clearSearchResults()
  await store.searchBangumi(item.id)
}

function handleClear() {
  store.clearSearchResults()
}
</script>

<style scoped>
.search-panel {
  padding: 28px 24px 20px;
  border-bottom: 1px solid var(--border-color);
}

.search-header {
  margin-bottom: 24px;
}

.app-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 6px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.back-home {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  flex-shrink: 0;
}

.back-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary-color), #a855f7);
  color: #fff;
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.back-arrow:hover {
  transform: translateX(-3px) scale(1.1);
  box-shadow: 0 4px 14px rgba(64, 158, 255, 0.4);
}

.app-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.search-input-group {
  display: flex;
  gap: 8px;
}

.search-input-group .el-input {
  flex: 1;
}

.search-results {
  margin-top: 12px;
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.results-list {
  max-height: 260px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background-color: rgba(64, 158, 255, 0.1);
}

.result-cover {
  flex-shrink: 0;
  width: 44px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--bg-color);
}

.result-cover.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.result-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.result-original {
  font-size: 11px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

.result-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.result-id {
  color: var(--primary-color);
  opacity: 0.7;
}

.error-message {
  margin-top: 12px;
}

.bangumi-info {
  display: flex;
  gap: 14px;
  margin-top: 16px;
  padding: 14px;
  background-color: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.bangumi-cover-wrapper {
  flex-shrink: 0;
  width: 80px;
  height: 110px;
  border-radius: 6px;
  overflow: hidden;
}

.bangumi-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.bangumi-details {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-width: 0;
}

.bangumi-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bangumi-original-title {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bangumi-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
