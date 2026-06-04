<template>
  <div class="tools-home">
    <header class="top-bar">
      <router-link to="/" class="logo">
        <span class="logo-icon">✦</span>
        <span class="logo-text">Toolbox</span>
      </router-link>
      <span class="page-name">实用工具</span>
    </header>

    <main class="content">
      <section class="hero">
        <h1>实用工具箱</h1>
        <p>日常工作生活必备工具合集，简单实用，无需安装</p>
      </section>

      <div class="tool-grid">
        <router-link
          v-for="tool in tools"
          :key="tool.id"
          class="tool-card"
          :to="tool.route"
        >
          <div class="tool-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path v-if="tool.id === 'qrcode'" d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/>
              <path v-else-if="tool.id === 'base64'" d="M4 7V4h16v3M9 20h6M12 4v16"/>
              <path v-else-if="tool.id === 'image'" d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3 3.5-4.5 4.5 6H4l4.5-4.5z"/>
              <path v-else-if="tool.id === 'pdf'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            </svg>
          </div>
          <div class="tool-info">
            <h3>{{ tool.title }}</h3>
            <p>{{ tool.desc }}</p>
          </div>
        </router-link>
      </div>
    </main>
  </div>
</template>

<script setup>
const tools = [
  {
    id: 'qrcode',
    route: '/tools/qrcode',
    title: '二维码工具',
    desc: '生成二维码图片，识别解析二维码内容',
  },
  {
    id: 'base64',
    route: '/tools/base64',
    title: 'Base64 编解码',
    desc: '文字与 Base64 互转，图片转 Base64 字符串',
  },
  {
    id: 'image',
    route: '/tools/image',
    title: '图片处理',
    desc: '图片格式转换，基础图片编辑处理',
  },
  {
    id: 'pdf',
    route: '/tools/pdf',
    title: 'PDF 转换',
    desc: 'PDF 转 Word/图片，图片转 PDF',
  },
]
</script>

<style scoped>
.tools-home {
  min-height: 100vh;
  background: var(--bg-primary, #ffffff);
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

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #7c3aed, #a78bfa);
  border-radius: 8px;
  color: white;
  font-size: 16px;
  font-weight: 700;
}

.logo-text {
  font-size: 16px;
  font-weight: 500;
  color: oklch(0.145 0 0);
}

.page-name {
  font-size: 14px;
  color: oklch(0.556 0 0);
  padding-left: 16px;
  border-left: 1px solid rgba(0, 0, 0, 0.08);
}

.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 32px 80px;
}

.hero {
  text-align: center;
  padding: 64px 0 48px;
}

.hero h1 {
  font-size: 32px;
  font-weight: 500;
  color: oklch(0.145 0 0);
  letter-spacing: -0.02em;
  margin-bottom: 12px;
}

.hero p {
  font-size: 15px;
  color: oklch(0.556 0 0);
  max-width: 480px;
  margin: 0 auto;
  line-height: 1.6;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.tool-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.2s ease;
}

.tool-card:hover {
  border-color: rgba(124, 58, 237, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.tool-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: oklch(0.97 0 0);
  border-radius: 10px;
  color: oklch(0.556 0 0);
  flex-shrink: 0;
}

.tool-info h3 {
  font-size: 16px;
  font-weight: 500;
  color: oklch(0.145 0 0);
  margin-bottom: 4px;
}

.tool-info p {
  font-size: 13px;
  color: oklch(0.556 0 0);
  line-height: 1.5;
}

@media (max-width: 640px) {
  .tool-grid {
    grid-template-columns: 1fr;
  }
  
  .content {
    padding: 0 20px 60px;
  }
  
  .hero {
    padding: 48px 0 32px;
  }
  
  .hero h1 {
    font-size: 26px;
  }
}
</style>
