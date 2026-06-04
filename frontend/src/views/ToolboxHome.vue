<template>
  <div class="toolbox-home">
    <header class="header">
      <div class="header-inner">
        <div class="logo">
          <div class="logo-mark">✦</div>
          <span class="logo-text">工具集</span>
        </div>
      </div>
    </header>

    <main class="main">
      <div class="hero">
        <h1>随便做的交互玩具</h1>
        <p>基于巴拉巴拉的大杂烩全栈交互应用集合</p>
      </div>

      <div class="grid">
        <router-link class="card" to="/camera">
          <div class="card-icon">📷</div>
          <div class="card-body">
            <span class="card-tag tag-active">Camera</span>
            <h3>摄像头交互工具</h3>
            <p>9 个基于摄像头的实时交互工具，包括 AR 背景替换、人脸贴纸、姿态识别、粒子艺术、手势控制 3D 等</p>
            <div class="tech">
              <span>MediaPipe</span>
              <span>Three.js</span>
              <span>WebGL</span>
              <span>9 个工具</span>
            </div>
          </div>
        </router-link>

        <router-link class="card" to="/life">
          <div class="card-icon">🎭</div>
          <div class="card-body">
            <span class="card-tag tag-active">AI 驱动</span>
            <h3>人生模拟器</h3>
            <p>选择世界观（现代/古代/未来），AI 驱动多分支人生剧情，逐字打字机沉浸式体验，每次选择改变命运走向</p>
            <div class="tech">
              <span>Django</span>
              <span>AI 大模型</span>
              <span>多分支剧情</span>
              <span>3 个世界</span>
            </div>
          </div>
        </router-link>

        <div class="card" @click="openAnimeTravel">
          <div class="card-icon">🎌</div>
          <div class="card-body">
            <span class="card-tag tag-active">AI 推荐</span>
            <h3>动漫巡礼</h3>
            <p>基于地理位置的动漫圣地巡礼推荐，结合 AI 分析动漫剧情取景地，跟随动漫主角的脚步探索现实世界</p>
            <div class="tech">
              <span>Leaflet</span>
              <span>AI 大模型</span>
              <span>地图服务</span>
            </div>
          </div>
        </div>

        <router-link class="card" to="/tools">
          <div class="card-icon">🛠️</div>
          <div class="card-body">
            <span class="card-tag tag-active">实用工具</span>
            <h3>实用工具箱</h3>
            <p>二维码生成/识别、Base64 编解码、图片格式转换、PDF 转换处理，常用工具一站式解决</p>
            <div class="tech">
              <span>QR Code</span>
              <span>Base64</span>
              <span>图片处理</span>
              <span>PDF 转换</span>
            </div>
          </div>
        </router-link>

      
      </div>
    </main>


  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

const router = useRouter()

const sakuraTheme = {
  color: [
    '#e52c3c', '#f7b1ab', '#fa506c', '#f59288', '#f8c4d8',
    '#e54f5c', '#f06d5c', '#e54f80', '#f29c9f', '#eeb5b7'
  ],
  title: {
    textStyle: { fontWeight: 'normal', color: '#e52c3c' }
  },
  visualMap: {
    color: ['#e52c3c', '#f7b1ab']
  },
  dataRange: {
    color: ['#e52c3c', '#f7b1ab']
  },
  candlestick: {
    itemStyle: { color: '#e52c3c', color0: '#f59288' },
    lineStyle: { width: 1, color: '#e52c3c', color0: '#f59288' },
    areaStyle: { color: '#fa506c', color0: '#f8c4d8' }
  },
  map: {
    itemStyle: { color: '#e52c3c', borderColor: '#fff', borderWidth: 1 },
    areaStyle: { color: '#ccc' },
    label: { color: 'rgba(139,69,19,1)', show: false }
  },
  graph: {
    itemStyle: { color: '#f2385a' },
    nodeStyle: { brushType: 'both', strokeColor: '#e54f5c' },
    linkStyle: { color: '#f2385a', strokeColor: '#e54f5c' },
    label: { color: '#f2385a', show: false }
  },
  gauge: {
    axisLine: {
      lineStyle: {
        color: [[0.2, '#e52c3c'], [0.8, '#f7b1ab'], [1, '#fa506c']],
        width: 8
      }
    }
  }
}

echarts.registerTheme('sakura', sakuraTheme)

function openAnimeTravel() {
  router.push('/anime-travel')
}
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(250, 249, 247, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #e5e5e5;
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 32px;
  display: flex;
  align-items: center;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-mark {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #7c3aed, #a78bfa);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  font-weight: 700;
}
.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.3px;
}
.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px;
}
.hero {
  text-align: center;
  padding: 80px 0 60px;
}
.hero h1 {
  font-size: 40px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.5px;
  margin-bottom: 16px;
}
.hero p {
  color: #6b6b6b;
  font-size: 16px;
  max-width: 500px;
  margin: 0 auto;
  line-height: 1.6;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding-bottom: 80px;
}
.card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
  cursor: pointer;
  display: block;
}
.card:hover:not(.disabled) {
  border-color: #d4d4d4;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}
.card.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.card-icon {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
}
.card-body {
  padding: 24px;
}
.card-tag {
  display: inline-block;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  margin-bottom: 12px;
  font-weight: 500;
}
.tag-active {
  background: #f3f0ff;
  color: #7c3aed;
}
.tag-coming {
  background: #f5f5f5;
  color: #999;
}
.card h3 {
  font-size: 17px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #1a1a1a;
}
.card p {
  font-size: 13px;
  color: #6b6b6b;
  line-height: 1.7;
}
.tech {
  margin-top: 16px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tech span {
  font-size: 11px;
  padding: 3px 10px;
  background: #f5f5f5;
  border-radius: 6px;
  color: #666;
}
.footer {
  text-align: center;
  padding: 32px;
  color: #aaa;
  font-size: 13px;
  border-top: 1px solid #e8e8e8;
}
</style>