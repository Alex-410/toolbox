<template>
  <div class="tool-page">
    <header class="top-bar">
      <router-link to="/tools" class="back-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </router-link>
      <span class="page-title">Base64 编解码</span>
    </header>

    <main class="content">
      <div class="tabs">
        <button :class="['tab', { active: activeTab === 'text' }]" @click="activeTab = 'text'">
          文字编解码
        </button>
        <button :class="['tab', { active: activeTab === 'encode' }]" @click="activeTab = 'encode'">
          图片转 Base64
        </button>
        <button :class="['tab', { active: activeTab === 'decode' }]" @click="activeTab = 'decode'">
          Base64 转图片
        </button>
      </div>

      <div v-if="activeTab === 'text'" class="form-card">
        <div class="form-group">
          <label>输入内容</label>
          <textarea v-model="inputText" placeholder="请输入文字或 Base64 字符串..." rows="6"></textarea>
        </div>
        <div class="btn-group">
          <button class="btn-primary" @click="encodeBase64">编码 → Base64</button>
          <button class="btn-outline" @click="decodeBase64">解码 ← Base64</button>
        </div>
        <div v-if="outputText" class="result">
          <label>结果：</label>
          <textarea v-model="outputText" rows="6" readonly></textarea>
          <button class="btn-ghost" @click="copyText">复制结果</button>
        </div>
      </div>

      <div v-if="activeTab === 'encode'" class="form-card">
        <div class="upload-area" @click="triggerUpload">
          <input ref="fileInput" type="file" accept="image/*" @change="handleFileSelect" />
          <div v-if="!previewImage" class="upload-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3 3.5-4.5 4.5 6H4l4.5-4.5z"/>
            </svg>
            <p>点击上传图片</p>
          </div>
          <img v-else :src="previewImage" alt="预览" class="preview-image" />
        </div>
        <div v-if="previewImage" class="file-info">
          <span class="file-name">{{ fileName }}</span>
          <span class="file-size">{{ fileSize }}</span>
        </div>
        <button class="btn-primary" @click="imageToBase64" :disabled="!previewImage">
          转换为 Base64
        </button>
        <div v-if="imageBase64" class="result">
          <label>Base64 字符串：</label>
          <textarea v-model="imageBase64" rows="4" readonly class="code-text"></textarea>
          <div class="btn-row">
            <button class="btn-ghost" @click="copyBase64">复制字符串</button>
            <button class="btn-outline" @click="downloadBase64">下载 HTML</button>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'decode'" class="form-card">
        <div class="form-group">
          <label>输入 Base64 字符串</label>
          <textarea 
            v-model="base64Input" 
            placeholder="请粘贴 Base64 字符串（以 data:image/ 开头或纯 Base64 内容）..."
            rows="8"
          ></textarea>
        </div>
        <button class="btn-primary" @click="decodeToImage" :disabled="!base64Input">
          解析为图片
        </button>
        <div v-if="decodedImage" class="result">
          <label>解析结果：</label>
          <img :src="decodedImage" alt="解码图片" class="decoded-image" />
          <div class="btn-row">
            <button class="btn-outline" @click="downloadDecodedImage">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
              </svg>
              下载图片
            </button>
          </div>
        </div>
        <div v-if="decodeError" class="error-msg">
          {{ decodeError }}
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('text')
const inputText = ref('')
const outputText = ref('')
const fileInput = ref(null)
const previewImage = ref('')
const imageBase64 = ref('')
const fileName = ref('')
const fileSize = ref('')
const base64Input = ref('')
const decodedImage = ref('')
const decodeError = ref('')

function encodeBase64() {
  try {
    outputText.value = btoa(unescape(encodeURIComponent(inputText.value)))
  } catch (e) {
    outputText.value = '编码失败：' + e.message
  }
}

function decodeBase64() {
  try {
    outputText.value = decodeURIComponent(escape(atob(inputText.value)))
  } catch (e) {
    outputText.value = '解码失败，请检查 Base64 字符串是否正确'
  }
}

function copyText() {
  navigator.clipboard.writeText(outputText.value)
}

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (file) {
    fileName.value = file.name
    fileSize.value = (file.size / 1024).toFixed(1) + ' KB'
    const reader = new FileReader()
    reader.onload = (e) => {
      previewImage.value = e.target.result
      imageBase64.value = ''
    }
    reader.readAsDataURL(file)
  }
}

function imageToBase64() {
  if (previewImage.value) {
    imageBase64.value = previewImage.value
  }
}

function copyBase64() {
  navigator.clipboard.writeText(imageBase64.value)
}

function downloadBase64() {
  if (!imageBase64.value) return
  const html = `<!DOCTYPE html><html><head><title>Image</title></head><body><img src="${imageBase64.value}" /></body></html>`
  const blob = new Blob([html], { type: 'text/html' })
  const link = document.createElement('a')
  link.download = 'image.html'
  link.href = URL.createObjectURL(blob)
  link.click()
}

function decodeToImage() {
  decodeError.value = ''
  decodedImage.value = ''
  
  let base64Data = base64Input.value.trim()
  
  if (!base64Data) {
    decodeError.value = '请输入 Base64 字符串'
    return
  }
  
  try {
    if (!base64Data.startsWith('data:')) {
      const isImage = base64Data.match(/^[A-Za-z0-9+/=]+$/)
      if (isImage && base64Data.length > 100) {
        base64Data = 'data:image/png;base64,' + base64Data
      } else {
        decodeError.value = '无效的 Base64 格式'
        return
      }
    }
    
    const img = new Image()
    img.onload = () => {
      decodedImage.value = base64Data
    }
    img.onerror = () => {
      decodeError.value = '无法解析为图片，请检查 Base64 字符串是否正确'
    }
    img.src = base64Data
  } catch (e) {
    decodeError.value = '解析失败：' + e.message
  }
}

function downloadDecodedImage() {
  if (!decodedImage.value) return
  
  const link = document.createElement('a')
  link.download = 'decoded_image.png'
  link.href = decodedImage.value
  link.click()
}
</script>

<style scoped>
.tool-page {
  min-height: 100vh;
  background: #ffffff;
}

.top-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 32px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: oklch(0.556 0 0);
  text-decoration: none;
}

.back-link:hover {
  color: oklch(0.145 0 0);
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: oklch(0.145 0 0);
}

.content {
  max-width: 600px;
  margin: 0 auto;
  padding: 48px 24px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab {
  flex: 1;
  padding: 10px 8px;
  background: oklch(0.97 0 0);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  font-size: 13px;
  color: oklch(0.556 0 0);
  cursor: pointer;
  transition: all 0.2s;
}

.tab.active {
  background: oklch(0.145 0 0);
  color: #ffffff;
  border-color: oklch(0.145 0 0);
}

.form-card {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: oklch(0.145 0 0);
  margin-bottom: 8px;
}

.form-group textarea,
.result textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 13px;
  resize: vertical;
  box-sizing: border-box;
  font-family: 'SF Mono', Monaco, monospace;
  color: oklch(0.145 0 0);
  background: #ffffff;
}

.form-group textarea:focus,
.result textarea:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

.form-group textarea::placeholder,
.result textarea::placeholder {
  color: oklch(0.7 0 0);
}

.btn-group {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.btn-primary {
  flex: 1;
  padding: 12px 20px;
  background: oklch(0.145 0 0);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-outline {
  flex: 1;
  padding: 12px 20px;
  background: #ffffff;
  color: oklch(0.145 0 0);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-outline:hover {
  border-color: rgba(0, 0, 0, 0.2);
}

.btn-ghost {
  padding: 8px 16px;
  background: transparent;
  color: oklch(0.556 0 0);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ghost:hover {
  color: oklch(0.145 0 0);
  background: oklch(0.97 0 0);
}

.result {
  margin-top: 20px;
}

.result label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: oklch(0.145 0 0);
  margin-bottom: 8px;
}

.result textarea {
  background: oklch(0.98 0 0);
}

.code-text {
  word-break: break-all;
}

.btn-row {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.upload-area {
  border: 2px dashed rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 16px;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #7c3aed;
}

.upload-area input[type="file"] {
  display: none;
}

.upload-placeholder {
  color: oklch(0.556 0 0);
}

.upload-placeholder svg {
  margin-bottom: 8px;
  color: oklch(0.7 0 0);
}

.preview-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
}

.file-info {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 12px;
  color: oklch(0.556 0 0);
}

.decoded-image {
  max-width: 100%;
  border-radius: 8px;
  margin-top: 12px;
}

.error-msg {
  margin-top: 16px;
  padding: 12px;
  background: #fef2f2;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
}
</style>
