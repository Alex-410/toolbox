<template>
  <div class="rag-page">
    <div class="header">
      <a href="/" class="back-link">
        <span class="back-icon">←</span>
        <span>返回工具箱</span>
      </a>
      <h1>RAG 知识库</h1>
    </div>

    <div class="content">
      <div class="upload-section">
        <div class="upload-card glass">
          <h3>📄 文档上传</h3>
          <div class="upload-area">
            <input type="file" id="file-input" accept=".txt,.md,.pdf" @change="handleFileSelect" />
            <label for="file-input" class="upload-btn">
              选择文件
            </label>
            <span class="file-name">{{ selectedFile?.name || '未选择文件' }}</span>
          </div>
          
          <div class="options">
            <div class="option">
              <label>切片策略：</label>
              <select v-model="chunkStrategy">
                <option value="fixed">固定长度</option>
                <option value="recursive">递归切片</option>
              </select>
            </div>
            <div class="option">
              <label>chunk_size：</label>
              <input type="number" v-model="chunkSize" min="100" max="2000" step="100" />
            </div>
            <div class="option">
              <label>overlap：</label>
              <input type="number" v-model="overlap" min="0" max="500" step="50" />
            </div>
          </div>
          
          <button class="upload-submit" @click="uploadFile" :disabled="uploading || !selectedFile">
            {{ uploading ? '解析中...' : '上传并预览切片' }}
          </button>
          
          <div v-if="uploadResult?.preview" class="preview-hint">
            ✅ 解析成功！请在下方预览并选择要保存的切片
          </div>
          
          <div v-if="uploadResult?.error" class="upload-result error">
            {{ uploadResult.error }}
          </div>
        </div>
        
        <div class="status-card glass">
          <h3>📚 知识库状态</h3>
          <div class="status-info">
            <span>文档数量：{{ status.doc_count || 0 }}</span>
            <span>向量索引：{{ status.has_index ? '✅ 已构建' : '❌ 未构建' }}</span>
            <span class="model-info">向量模型：{{ status.embedding_model || '-' }}</span>
          </div>
          
          <div v-if="status.docs && status.docs.length > 0" class="docs-list">
            <div v-for="doc in status.docs" :key="doc.filename" class="doc-item">
              <span class="doc-name">{{ doc.filename }} ({{ doc.count }} 个切片)</span>
              <button class="delete-btn" @click="deleteDoc(doc.filename)">🗑️</button>
            </div>
          </div>
          
          <button class="refresh-btn" @click="loadStatus">🔄 刷新状态</button>
        </div>
      </div>

      <div v-if="previewChunks.length > 0" class="preview-section glass">
        <div class="preview-header">
          <h3>✂️ 切片预览 - {{ uploadResult?.filename }}</h3>
          <div class="preview-actions">
            <button class="select-all-btn" @click="selectAll">{{ allSelected ? '取消全选' : '全选' }}</button>
            <button class="save-btn" @click="saveChunks" :disabled="saving">
              {{ saving ? '保存中...' : `保存已选切片 (${selectedCount})` }}
            </button>
          </div>
        </div>
        <div class="chunks-list">
          <div v-for="chunk in previewChunks" :key="chunk.index" class="chunk-item" :class="{ selected: chunk.selected }">
            <label class="chunk-checkbox">
              <input type="checkbox" v-model="chunk.selected" />
              <span class="chunk-index">#{{ chunk.index + 1 }}</span>
            </label>
            <div class="chunk-content">{{ chunk.content }}</div>
          </div>
        </div>
      </div>

      <div class="chat-section glass">
        <div class="chat-header">
          <h3>💬 智能问答</h3>
          <div class="chat-actions">
            <label class="rerank-toggle">
              <input type="checkbox" v-model="useRerank" />
              <span>启用 Rerank</span>
            </label>
            <button class="clear-btn" @click="clearHistory">🗑️ 清空历史</button>
          </div>
        </div>
        
        <div class="chat-messages" ref="chatContainer">
          <div v-if="history.length === 0" class="empty-hint">
            上传文档后，开始提问吧~
          </div>
          <div v-for="(msg, i) in history" :key="i" class="message" :class="msg.role">
            <div class="message-content">{{ msg.content }}</div>
          </div>
          <div v-if="loading" class="message assistant">
            <div class="message-content">思考中...</div>
          </div>
        </div>
        
        <div class="chat-input">
          <input
            v-model="question"
            type="text"
            placeholder="输入问题..."
            @keydown.enter="sendQuestion"
            :disabled="loading"
          />
          <button @click="sendQuestion" :disabled="loading || !question.trim()">发送</button>
        </div>
      </div>

      <div v-if="retrievedChunks.length > 0" class="retrieved-section glass">
        <h3>📎 检索到的片段</h3>
        <div class="chunks-list">
          <div v-for="(chunk, i) in retrievedChunks" :key="i" class="chunk-item">
            <div class="chunk-header">
              <span class="chunk-source">{{ chunk.filename }}</span>
              <span class="chunk-score">相似度: {{ (1 - chunk.score / 10).toFixed(2) }}</span>
            </div>
            <div class="chunk-content">{{ chunk.content }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'

const selectedFile = ref(null)
const chunkStrategy = ref('fixed')
const chunkSize = ref(500)
const overlap = ref(50)
const uploading = ref(false)
const saving = ref(false)
const uploadResult = ref(null)
const previewChunks = ref([])
const status = ref({})
const question = ref('')
const loading = ref(false)
const history = ref([])
const retrievedChunks = ref([])
const chatContainer = ref(null)
const useRerank = ref(false)

const allSelected = computed(() => {
  return previewChunks.value.length > 0 && previewChunks.value.every(c => c.selected)
})

const selectedCount = computed(() => {
  return previewChunks.value.filter(c => c.selected).length
})

function handleFileSelect(e) {
  selectedFile.value = e.target.files[0]
  uploadResult.value = null
  previewChunks.value = []
}

async function uploadFile() {
  if (!selectedFile.value) return
  
  uploading.value = true
  uploadResult.value = null
  previewChunks.value = []
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('strategy', chunkStrategy.value)
  formData.append('chunk_size', chunkSize.value)
  formData.append('overlap', overlap.value)
  
  try {
    const res = await fetch('/api/rag/upload/', {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    uploadResult.value = data
    if (data.preview) {
      previewChunks.value = data.chunks || []
    }
  } catch (e) {
    uploadResult.value = { error: '上传失败: ' + e.message }
  } finally {
    uploading.value = false
  }
}

function selectAll() {
  const newValue = !allSelected.value
  previewChunks.value.forEach(c => c.selected = newValue)
}

async function saveChunks() {
  if (selectedCount.value === 0) {
    alert('请至少选择一个切片')
    return
  }
  
  saving.value = true
  
  try {
    const selectedContents = previewChunks.value
      .filter(c => c.selected)
      .map(c => c.content)
    
    const res = await fetch('/api/rag/save/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: uploadResult.value.filename,
        strategy: uploadResult.value.strategy,
        selected_chunks: selectedContents
      })
    })
    const data = await res.json()
    
    if (data.success) {
      uploadResult.value = { success: true, chunks: data.chunks }
      previewChunks.value = []
      loadStatus()
    } else {
      alert(data.error || '保存失败')
    }
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

async function loadStatus() {
  try {
    const res = await fetch('/api/rag/status/')
    status.value = await res.json()
  } catch (e) {
    console.error(e)
  }
}

async function deleteDoc(filename) {
  if (!confirm(`确定要删除 "${filename}" 吗？`)) return
  
  try {
    const res = await fetch('/api/rag/delete/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename })
    })
    const data = await res.json()
    
    if (data.success) {
      loadStatus()
    } else {
      alert(data.error || '删除失败')
    }
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

async function loadHistory() {
  try {
    const res = await fetch('/api/rag/history/')
    const data = await res.json()
    history.value = data.history || []
    scrollToBottom()
  } catch (e) {
    console.error(e)
  }
}

async function sendQuestion() {
  if (!question.value.trim() || loading.value) return
  
  const q = question.value.trim()
  question.value = ''
  loading.value = true
  
  try {
    const res = await fetch('/api/rag/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, use_rerank: useRerank.value }),
    })
    const data = await res.json()
    
    if (data.error) {
      history.value.push({ role: 'user', content: q })
      history.value.push({ role: 'assistant', content: data.error })
    } else {
      history.value = data.history || []
      retrievedChunks.value = data.retrieved_chunks || []
    }
  } catch (e) {
    history.value.push({ role: 'user', content: q })
    history.value.push({ role: 'assistant', content: '请求失败: ' + e.message })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function clearHistory() {
  if (!confirm('确定清空对话历史？')) return
  
  try {
    await fetch('/api/rag/clear/', { method: 'POST' })
    history.value = []
    retrievedChunks.value = []
  } catch (e) {
    console.error(e)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  loadStatus()
  loadHistory()
})
</script>

<style scoped>
.rag-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e4de 50%, #f0ebe5 100%);
  padding: 24px;
}

.header {
  max-width: 900px;
  margin: 0 auto 24px;
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

.header h1 {
  color: #333;
  font-size: 28px;
  font-weight: 600;
}

.content {
  max-width: 900px;
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

.upload-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.upload-card,
.status-card {
  padding: 24px;
}

.upload-card h3,
.status-card h3,
.chat-section h3,
.retrieved-section h3 {
  color: #333;
  font-size: 16px;
  margin-bottom: 16px;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.upload-area input[type="file"] {
  display: none;
}

.upload-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.file-name {
  color: #666;
  font-size: 13px;
}

.options {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option label {
  color: #666;
  font-size: 13px;
}

.option select,
.option input {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.8);
  color: #333;
  font-size: 13px;
  outline: none;
}

.option input {
  width: 80px;
}

.upload-submit {
  width: 100%;
  padding: 14px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}

.upload-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.upload-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-result {
  margin-top: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(46, 213, 115, 0.15);
  color: #2ed573;
  font-size: 13px;
}

.upload-result.error {
  background: rgba(255, 71, 87, 0.15);
  color: #ff4757;
}

.preview-hint {
  margin-top: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(46, 213, 115, 0.15);
  color: #2ed573;
  font-size: 13px;
}

.preview-section {
  margin-bottom: 24px;
  padding: 24px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.preview-header h3 {
  margin: 0;
}

.preview-actions {
  display: flex;
  gap: 12px;
}

.select-all-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  background: rgba(255, 255, 255, 0.6);
  color: #667eea;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.select-all-btn:hover {
  background: rgba(102, 126, 234, 0.1);
}

.save-btn {
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-section .chunks-list {
  max-height: 500px;
  overflow-y: auto;
}

.preview-section .chunk-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 10px;
  margin-bottom: 10px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.preview-section .chunk-item.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.chunk-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  flex-shrink: 0;
}

.chunk-checkbox input {
  margin-top: 4px;
}

.chunk-index {
  color: #667eea;
  font-weight: 500;
  font-size: 12px;
  min-width: 32px;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  color: #666;
  font-size: 13px;
}

.model-info {
  font-size: 12px;
  color: #999;
}

.docs-list {
  margin: 12px 0;
  padding: 12px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 10px;
}

.doc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.doc-item:last-child {
  border-bottom: none;
}

.doc-name {
  font-size: 13px;
  color: #333;
}

.delete-btn {
  padding: 4px 8px;
  border-radius: 6px;
  border: none;
  background: rgba(255, 71, 87, 0.1);
  color: #ff4757;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.delete-btn:hover {
  background: rgba(255, 71, 87, 0.2);
}

.refresh-btn {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.6);
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.9);
}

.chat-section {
  padding: 24px;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chat-header h3 {
  margin: 0;
}

.chat-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rerank-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
}

.rerank-toggle input {
  cursor: pointer;
}

.clear-btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 71, 87, 0.3);
  background: rgba(255, 255, 255, 0.6);
  color: #ff4757;
  font-size: 12px;
  cursor: pointer;
}

.chat-messages {
  height: 320px;
  overflow-y: auto;
  margin-bottom: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
}

.empty-hint {
  color: #999;
  text-align: center;
  padding: 40px;
}

.message {
  margin-bottom: 12px;
}

.message.user {
  text-align: right;
}

.message-content {
  display: inline-block;
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}

.message.assistant .message-content {
  background: rgba(255, 255, 255, 0.9);
  color: #333;
}

.chat-input {
  display: flex;
  gap: 12px;
}

.chat-input input {
  flex: 1;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.8);
  color: #333;
  font-size: 14px;
  outline: none;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.04);
}

.chat-input input:focus {
  border-color: #667eea;
}

.chat-input button {
  padding: 14px 28px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.chat-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.retrieved-section {
  margin-top: 24px;
  padding: 24px;
}

.chunks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.chunk-item {
  padding: 14px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.chunk-source {
  color: #667eea;
  font-size: 12px;
  font-weight: 500;
}

.chunk-score {
  color: #999;
  font-size: 12px;
}

.chunk-content {
  color: #555;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
