<template>
  <div class="douyin-page">
    <div class="header">
      <a href="/tools" class="back-link">
        <span class="back-icon">←</span>
        <span>返回工具箱</span>
      </a>
      <h1>抖音视频下载</h1>
    </div>

    <div class="content">
      <div class="input-card">
        <div class="input-header">
          <span class="icon">🎵</span>
          <span>批量解析抖音链接</span>
          <button class="add-btn" @click="addInput">+ 新增</button>
        </div>

        <div class="input-list">
          <div v-for="(item, index) in inputs" :key="index" class="input-item">
            <input
              v-model="item.url"
              type="text"
              :placeholder="`第 ${index + 1} 个链接，如：https://v.douyin.com/xxxxx`"
              @keydown.enter="downloadAll"
            />
            <button v-if="inputs.length > 1" class="remove-btn" @click="removeInput(index)">×</button>
          </div>
        </div>

        <div class="action-row">
          <button class="download-btn" @click="downloadAll" :disabled="loading">
            {{ loading ? '获取中...' : '批量获取' }}
          </button>
        </div>
      </div>

      <div v-if="results.length > 0" class="results">
        <div v-for="(r, i) in results" :key="i" class="result-card">
          <div class="result-header">
            <span class="icon">{{ r.success ? '✅' : '❌' }}</span>
            <span>{{ r.success ? `视频 ${i + 1}` : `失败 ${i + 1}` }}</span>
          </div>

          <template v-if="r.success">
            <div class="video-info">
              <p class="title">{{ r.title }}</p>
              <div class="url-box">
                <input :value="r.video_url" readonly />
                <button class="copy-btn" @click="copyUrl(r.video_url)">复制</button>
              </div>
            </div>
            <div class="actions">
              <a :href="r.video_url" target="_blank" class="open-btn">
                在浏览器打开
              </a>
            </div>
          </template>

          <template v-else>
            <p class="error">{{ r.error }}</p>
          </template>
        </div>
      </div>

      <div class="tips">
        <h3>使用说明</h3>
        <ul>
          <li>点击「+ 新增」按钮添加多个输入框</li>
          <li>在抖音APP中点击分享 → 复制链接</li>
          <li>将链接粘贴到输入框</li>
          <li>点击「批量获取」按钮</li>
          <li>复制生成的直链，在浏览器打开即可下载</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const inputs = ref([{ url: '' }])
const loading = ref(false)
const results = ref([])

function addInput() {
  inputs.value.push({ url: '' })
}

function removeInput(index) {
  inputs.value.splice(index, 1)
}

async function downloadAll() {
  const urls = inputs.value.map(i => i.url.trim()).filter(u => u)
  if (urls.length === 0) {
    results.value = [{ success: false, error: '请至少输入一个抖音链接' }]
    return
  }

  loading.value = true
  results.value = []

  for (const url of urls) {
    try {
      const res = await fetch('/api/douyin/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      const data = await res.json()

      if (data.error) {
        results.value.push({ success: false, error: data.error })
      } else {
        results.value.push({ success: true, title: data.title, video_url: data.video_url })
      }
    } catch (e) {
      results.value.push({ success: false, error: '请求失败' })
    }
  }

  loading.value = false
}

function copyUrl(url) {
  navigator.clipboard.writeText(url)
  alert('链接已复制到剪贴板')
}
</script>

<style scoped>
.douyin-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e4de 50%, #f0ebe5 100%);
  padding: 24px;
}

.header {
  max-width: 600px;
  margin: 0 auto 32px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #666;
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 16px;
  transition: color 0.2s;
}

.back-link:hover {
  color: #333;
}

.back-icon {
  font-size: 16px;
}

.header h1 {
  color: #333;
  font-size: 28px;
  font-weight: 600;
}

.content {
  max-width: 600px;
  margin: 0 auto;
}

.glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.input-card,
.result-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  padding: 24px;
}

.input-header {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #333;
  font-size: 16px;
  margin-bottom: 16px;
}

.input-header .icon {
  font-size: 20px;
}

.add-btn {
  margin-left: auto;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  background: rgba(255, 255, 255, 0.6);
  color: #667eea;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.input-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.input-item {
  display: flex;
  gap: 10px;
}

.input-item input {
  flex: 1;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.8);
  color: #333;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.input-item input::placeholder {
  color: #999;
}

.input-item input:focus {
  border-color: #667eea;
}

.remove-btn {
  width: 44px;
  border-radius: 10px;
  border: 1px solid rgba(255, 71, 87, 0.3);
  background: rgba(255, 255, 255, 0.6);
  color: #ff4757;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: rgba(255, 71, 87, 0.1);
}

.action-row {
  display: flex;
  justify-content: center;
}

.download-btn {
  padding: 14px 32px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.download-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.download-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.results {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  margin: 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #333;
  font-size: 14px;
  margin-bottom: 12px;
}

.result-header .icon {
  font-size: 16px;
}

.video-info {
  margin-bottom: 12px;
}

.title {
  color: #333;
  font-size: 14px;
  margin-bottom: 10px;
  line-height: 1.5;
}

.url-box {
  display: flex;
  gap: 10px;
}

.url-box input {
  flex: 1;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.8);
  color: #666;
  font-size: 12px;
}

.copy-btn {
  padding: 10px 16px;
  border-radius: 6px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.copy-btn:hover {
  background: linear-gradient(135deg, #5a6fd6, #6a4190);
}

.actions {
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.open-btn {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  text-decoration: none;
  font-size: 13px;
  transition: background 0.2s;
}

.open-btn:hover {
  background: linear-gradient(135deg, #5a6fd6, #6a4190);
}

.error {
  color: #ff4757;
  font-size: 13px;
}

.tips {
  margin-top: 32px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.tips h3 {
  color: #666;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
}

.tips ul {
  margin: 0;
  padding-left: 20px;
}

.tips li {
  color: #666;
  font-size: 13px;
  line-height: 1.8;
}
</style>
