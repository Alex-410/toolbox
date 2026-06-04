<template>
  <div class="tool-page">
    <header class="top-bar">
      <router-link to="/tools" class="back-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </router-link>
      <span class="page-title">PDF 转换</span>
    </header>

    <main class="content">
      <div class="tabs">
        <button :class="['tab', { active: activeTab === 'pdfToImg' }]" @click="activeTab = 'pdfToImg'">
          PDF 转图片
        </button>
        <button :class="['tab', { active: activeTab === 'imgToPdf' }]" @click="activeTab = 'imgToPdf'">
          图片转 PDF
        </button>
        <button :class="['tab', { active: activeTab === 'pdfToWord' }]" @click="activeTab = 'pdfToWord'">
          PDF 转 Word
        </button>
      </div>

      <div v-if="activeTab === 'pdfToImg'" class="form-card">
        <div class="upload-area" @click="triggerUploadPdf">
          <input ref="pdfInput" type="file" accept=".pdf" @change="handlePdfSelect" />
          <div v-if="!selectedPdf" class="upload-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <p>点击上传 PDF 文件</p>
          </div>
          <div v-else class="file-info">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            </svg>
            <span>{{ selectedPdf.name }}</span>
          </div>
        </div>
        
        <button class="btn-primary" @click="pdfToImages" :disabled="!selectedPdf || isProcessing">
          {{ isProcessing ? '处理中...' : 'PDF 转换为图片' }}
        </button>

        <div v-if="isProcessing" class="loading">
          <div class="spinner"></div>
          <span>正在转换，请稍候...</span>
        </div>

        <div v-if="convertedImages.length" class="result-grid">
          <div v-for="(img, i) in convertedImages" :key="i" class="result-item">
            <img :src="img" alt="" />
            <button class="btn-download" @click="downloadImage(img, `page-${i + 1}.png`)">
              下载
            </button>
          </div>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>

      <div v-if="activeTab === 'imgToPdf'" class="form-card">
        <div class="upload-area" @click="triggerUploadImgs">
          <input ref="imgInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple @change="handleImgSelect" />
          <div v-if="!selectedImages.length" class="upload-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            <p>点击上传图片（可多选）</p>
          </div>
          <div v-else class="image-list">
            <div v-for="(img, i) in selectedImages" :key="i" class="image-thumb">
              <img :src="img.preview" alt="" />
              <span>Page {{ i + 1 }}</span>
            </div>
          </div>
        </div>

        <div v-if="selectedImages.length" class="file-count">
          已选择 {{ selectedImages.length }} 张图片
        </div>

        <button class="btn-primary" @click="imagesToPdf" :disabled="!selectedImages.length || isProcessing">
          {{ isProcessing ? '处理中...' : '图片转换为 PDF' }}
        </button>

        <div v-if="isProcessing" class="loading">
          <div class="spinner"></div>
          <span>正在生成 PDF，请稍候...</span>
        </div>

        <div v-if="generatedPdf" class="result-area">
          <div class="success-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <p>PDF 已生成</p>
          <button class="btn-outline" @click="downloadPdf">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
            </svg>
            下载 PDF
          </button>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>

      <div v-if="activeTab === 'pdfToWord'" class="form-card">
        <div class="upload-area" @click="triggerUploadWord">
          <input ref="wordPdfInput" type="file" accept=".pdf" @change="handleWordPdfSelect" />
          <div v-if="!selectedWordPdf" class="upload-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            <p>点击上传 PDF 文件</p>
          </div>
          <div v-else class="file-info">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            </svg>
            <span>{{ selectedWordPdf.name }}</span>
          </div>
        </div>

        <button class="btn-primary" @click="pdfToWord" :disabled="!selectedWordPdf || isProcessing">
          {{ isProcessing ? '处理中...' : 'PDF 转换为 Word' }}
        </button>

        <div v-if="isProcessing" class="loading">
          <div class="spinner"></div>
          <span>正在提取文字，请稍候...</span>
        </div>

        <div v-if="wordContent" class="result">
          <label>提取的文字内容：</label>
          <textarea v-model="wordContent" rows="10" readonly></textarea>
          <div class="btn-row">
            <button class="btn-ghost" @click="copyWordContent">复制内容</button>
            <button class="btn-outline" @click="downloadWordContent">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
              </svg>
              下载文本
            </button>
          </div>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = '/api/pdf'

const activeTab = ref('pdfToImg')
const pdfInput = ref(null)
const imgInput = ref(null)
const wordPdfInput = ref(null)
const selectedPdf = ref(null)
const selectedImages = ref([])
const selectedWordPdf = ref(null)
const convertedImages = ref([])
const generatedPdf = ref('')
const wordContent = ref('')
const isProcessing = ref(false)
const errorMsg = ref('')

function triggerUploadPdf() {
  pdfInput.value?.click()
}
function triggerUploadImgs() {
  imgInput.value?.click()
}
function triggerUploadWord() {
  wordPdfInput.value?.click()
}

function handlePdfSelect(e) {
  const file = e.target.files?.[0]
  if (file) {
    selectedPdf.value = file
    convertedImages.value = []
    errorMsg.value = ''
  }
}

function handleImgSelect(e) {
  const files = Array.from(e.target.files || [])
  selectedImages.value = files.map(file => ({
    file,
    preview: URL.createObjectURL(file)
  }))
  generatedPdf.value = ''
  errorMsg.value = ''
}

function handleWordPdfSelect(e) {
  const file = e.target.files?.[0]
  if (file) {
    selectedWordPdf.value = file
    wordContent.value = ''
    errorMsg.value = ''
  }
}

async function pdfToImages() {
  if (!selectedPdf.value) return
  isProcessing.value = true
  errorMsg.value = ''
  convertedImages.value = []

  const formData = new FormData()
  formData.append('file', selectedPdf.value)

  try {
    const res = await fetch(`${API_BASE}/pdf-to-images/`, {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    
    if (data.success) {
      convertedImages.value = data.images.map(img => img.image)
    } else {
      errorMsg.value = data.error || '转换失败'
    }
  } catch (e) {
    errorMsg.value = '请求失败：' + e.message
  } finally {
    isProcessing.value = false
  }
}

function downloadImage(dataUrl, filename) {
  const link = document.createElement('a')
  link.download = filename
  link.href = dataUrl
  link.click()
}

async function imagesToPdf() {
  if (!selectedImages.value.length) return
  isProcessing.value = true
  errorMsg.value = ''
  generatedPdf.value = ''

  const formData = new FormData()
  selectedImages.value.forEach(item => {
    formData.append('images', item.file)
  })

  try {
    const res = await fetch(`${API_BASE}/images-to-pdf/`, {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    
    if (data.success) {
      generatedPdf.value = data.pdf
    } else {
      errorMsg.value = data.error || '转换失败'
    }
  } catch (e) {
    errorMsg.value = '请求失败：' + e.message
  } finally {
    isProcessing.value = false
  }
}

function downloadPdf() {
  if (generatedPdf.value) {
    const link = document.createElement('a')
    link.download = 'converted.pdf'
    link.href = generatedPdf.value
    link.click()
  }
}

async function pdfToWord() {
  if (!selectedWordPdf.value) return
  isProcessing.value = true
  errorMsg.value = ''
  wordContent.value = ''

  const formData = new FormData()
  formData.append('file', selectedWordPdf.value)

  try {
    const res = await fetch(`${API_BASE}/pdf-to-word/`, {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    
    if (data.success) {
      wordContent.value = data.content
    } else {
      errorMsg.value = data.error || '转换失败'
    }
  } catch (e) {
    errorMsg.value = '请求失败：' + e.message
  } finally {
    isProcessing.value = false
  }
}

function copyWordContent() {
  navigator.clipboard.writeText(wordContent.value)
}

function downloadWordContent() {
  if (!wordContent.value) return
  const blob = new Blob([wordContent.value], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.download = 'extracted_text.txt'
  link.href = URL.createObjectURL(blob)
  link.click()
  URL.revokeObjectURL(link.href)
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
  max-width: 700px;
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
  font-size: 12px;
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

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: oklch(0.145 0 0);
}

.file-info svg {
  color: oklch(0.556 0 0);
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.image-thumb {
  width: 80px;
  text-align: center;
}

.image-thumb img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.image-thumb span {
  font-size: 11px;
  color: oklch(0.7 0 0);
  display: block;
  margin-top: 4px;
}

.file-count {
  text-align: center;
  font-size: 14px;
  color: oklch(0.556 0 0);
  margin-bottom: 12px;
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
  margin-bottom: 20px;
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
}

.btn-ghost:hover {
  color: oklch(0.145 0 0);
  background: oklch(0.97 0 0);
}

.btn-download {
  margin-top: 8px;
  padding: 6px 12px;
  background: oklch(0.97 0 0);
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  color: oklch(0.556 0 0);
  font-size: 14px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid oklch(0.92 0 0);
  border-top-color: oklch(0.556 0 0);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.result-item {
  text-align: center;
}

.result-item img {
  width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.result-area {
  text-align: center;
  margin-top: 20px;
  padding: 24px;
  background: oklch(0.98 0 0);
  border-radius: 12px;
}

.success-icon {
  color: #16a34a;
  margin-bottom: 8px;
}

.result-area p {
  color: #16a34a;
  margin-bottom: 12px;
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
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 13px;
  resize: vertical;
  box-sizing: border-box;
  font-family: monospace;
  background: oklch(0.98 0 0);
}

.btn-row {
  display: flex;
  gap: 12px;
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
