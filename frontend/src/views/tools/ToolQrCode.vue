<template>
  <div class="tool-page">
    <header class="top-bar">
      <router-link to="/tools" class="back-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </router-link>
      <span class="page-title">二维码工具</span>
    </header>

    <main class="content">
      <div class="tabs">
        <button :class="['tab', { active: activeTab === 'generate' }]" @click="activeTab = 'generate'">
          生成二维码
        </button>
        <button :class="['tab', { active: activeTab === 'recognize' }]" @click="activeTab = 'recognize'">
          识别二维码
        </button>
      </div>

      <div v-if="activeTab === 'generate'" class="form-card">
        <div class="form-group">
          <label>输入内容（网址或文字）</label>
          <textarea 
            v-model="inputText" 
            placeholder="请输入网址或文字..."
            rows="4"
          ></textarea>
        </div>
        <button class="btn-primary" @click="generateQRCode" :disabled="!inputText">
          生成二维码
        </button>
        <div v-if="qrCodeData" class="result">
          <img :src="qrCodeData" alt="二维码" class="qr-image" />
          <button class="btn-outline" @click="downloadQRCode">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
            </svg>
            下载图片
          </button>
        </div>
      </div>

      <div v-if="activeTab === 'recognize'" class="form-card">
        <div class="upload-area" @click="triggerUpload">
          <input ref="fileInput" type="file" accept="image/*" @change="handleFileSelect" />
          <div v-if="!selectedImage" class="upload-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            <p>点击上传二维码图片</p>
          </div>
          <img v-else :src="selectedImage" alt="上传的图片" class="preview-image" />
        </div>
        <button class="btn-primary" @click="recognizeQRCode" :disabled="!selectedImage || isRecognizing">
          {{ isRecognizing ? '识别中...' : '识别二维码' }}
        </button>
        <div v-if="recognizedText" class="result">
          <label>识别结果：</label>
          <textarea v-model="recognizedText" rows="3" readonly></textarea>
          <button class="btn-ghost" @click="copyResult">复制结果</button>
        </div>
        <div v-if="recognizeError" class="error-msg">
          {{ recognizeError }}
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import jsQR from 'jsqr'

const activeTab = ref('generate')
const inputText = ref('')
const qrCodeData = ref('')
const fileInput = ref(null)
const selectedImage = ref('')
const recognizedText = ref('')
const isRecognizing = ref(false)
const recognizeError = ref('')

function generateQRCode() {
  if (!inputText.value) return
  const qrApi = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(inputText.value)}`
  qrCodeData.value = qrApi
}

function downloadQRCode() {
  if (!qrCodeData.value) return
  const link = document.createElement('a')
  link.download = 'qrcode.png'
  link.href = qrCodeData.value
  link.click()
}

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (file) {
    selectedImage.value = URL.createObjectURL(file)
    recognizedText.value = ''
    recognizeError.value = ''
  }
}

async function recognizeQRCode() {
  if (!selectedImage.value || isRecognizing.value) return
  
  isRecognizing.value = true
  recognizeError.value = ''
  recognizedText.value = ''

  try {
    const img = new Image()
    img.crossOrigin = 'Anonymous'
    img.src = selectedImage.value
    
    await new Promise((resolve, reject) => {
      img.onload = resolve
      img.onerror = reject
    })

    const canvas = document.createElement('canvas')
    canvas.width = img.width
    canvas.height = img.height
    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0)
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const code = jsQR(imageData.data, imageData.width, imageData.height)
    
    if (code && code.data) {
      recognizedText.value = code.data
    } else {
      recognizeError.value = '未识别到二维码，请确保图片清晰且包含二维码'
    }
  } catch (e) {
    recognizeError.value = '识别失败：' + e.message
  } finally {
    isRecognizing.value = false
  }
}

function copyResult() {
  navigator.clipboard.writeText(recognizedText.value)
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
  padding: 10px 16px;
  background: oklch(0.97 0 0);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  font-size: 14px;
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
  margin-bottom: 24px;
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
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
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

.btn-primary {
  width: 100%;
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
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #ffffff;
  color: oklch(0.145 0 0);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover {
  border-color: rgba(0, 0, 0, 0.2);
  background: oklch(0.98 0 0);
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
  margin-top: 24px;
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
  margin-bottom: 12px;
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

.qr-image {
  max-width: 250px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.upload-area {
  border: 2px dashed rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 20px;
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
</style>
