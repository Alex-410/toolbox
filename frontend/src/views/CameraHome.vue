<template>
  <div class="camera-home">
    <header class="top-bar">
      <router-link to="/" class="logo">
        <span class="logo-icon">🧰</span>
        <span class="logo-text">Toolbox</span>
      </router-link>
      <span class="page-name">Camera</span>
    </header>

    <section class="hero">
      <h1>摄像头交互工具</h1>
      <p>基于 MediaPipe + Three.js 的实时摄像头交互应用，选择下方工具开始体验</p>
    </section>

    <section class="grid">
      <router-link
        v-for="tool in tools"
        :key="tool.route"
        class="card"
        :to="tool.route"
      >
        <div class="card-icon" :style="{ background: 'linear-gradient(135deg, ' + tool.bg + ')' }">
          {{ tool.icon }}
        </div>
        <div class="card-body">
          <span class="card-tag" :class="tool.tagClass">{{ tool.tag }}</span>
          <h3>{{ tool.title }}</h3>
          <p>{{ tool.desc }}</p>
          <div class="tech">
            <span v-for="t in tool.techs" :key="t">{{ t }}</span>
          </div>
        </div>
      </router-link>
    </section>
  </div>
</template>

<script setup>
const tools = [
  {
    route: '/camera/ar-background',
    icon: '🌄',
    bg: '#f0fdf4, #dcfce7',
    tag: 'AR', tagClass: 'tag-green',
    title: 'AR 背景替换工具',
    desc: '实时人像分割 + 3D 虚拟背景叠加，支持自定义背景图片/视频，边缘柔化效果',
    techs: ['MediaPipe Selfie Segmentation', 'Three.js', 'Canvas']
  },
  {
    route: '/camera/face-sticker',
    icon: '😎',
    bg: '#f5f3ff, #ede9fe',
    tag: '人脸', tagClass: 'tag-purple',
    title: '3D 人脸贴纸相机',
    desc: 'MediaPipe 识别 468 个人脸关键点，3D 眼镜/帽子/面具模型自动贴合',
    techs: ['MediaPipe Face Mesh', 'Three.js', 'MediaRecorder']
  },
  {
    route: '/camera/pose-skeleton',
    icon: '🦴',
    bg: '#fff7ed, #ffedd5',
    tag: '姿势', tagClass: 'tag-orange',
    title: '姿势识别 + 3D 骨骼可视化',
    desc: 'MediaPipe 识别 33 个人体关键点，实时渲染可动 3D 骨骼模型',
    techs: ['MediaPipe Pose', 'Three.js', '骨骼动画']
  },
  {
    route: '/camera/particle-art',
    icon: '✨',
    bg: '#eff6ff, #dbeafe',
    tag: '艺术', tagClass: 'tag-blue',
    title: '摄像头粒子追踪艺术',
    desc: '手势控制粒子效果，支持吸引/排斥/漩涡/自由绘制/粒子球等多种交互模式',
    techs: ['MediaPipe Hands', 'Canvas 2D', '粒子系统']
  },
  {
    route: '/camera/camera-game',
    icon: '🎮',
    bg: '#fef2f2, #fee2e2',
    tag: '游戏', tagClass: 'tag-red',
    title: '摄像头控制 3D 小游戏',
    desc: '通过挥手/跳跃动作控制 3D 角色移动，收集道具得分',
    techs: ['MediaPipe Pose', 'Three.js', '物理引擎']
  },
  {
    route: '/camera/distortion',
    icon: '🌀',
    bg: '#ecfdf5, #d1fae5',
    tag: '3D', tagClass: 'tag-teal',
    title: '实时 3D 扭曲相机',
    desc: '摄像头画面映射到可变形 3D 几何体上，支持多种模型和特效调整',
    techs: ['Three.js', 'Vertex Shader', 'WebGL']
  },
  {
    route: '/camera/webxr-ar',
    icon: '🌐',
    bg: '#fefce8, #fef9c3',
    tag: 'WebXR', tagClass: 'tag-yellow',
    title: 'WebXR 摄像头 AR 应用',
    desc: '将 3D 模型固定在真实空间中，支持模型缩放旋转',
    techs: ['WebXR API', 'Three.js', 'AR Hit Test']
  },
  {
    route: '/camera/point-cloud',
    icon: '☁️',
    bg: '#faf5ff, #f3e8ff',
    tag: '点云', tagClass: 'tag-violet',
    title: '深度图 3D 点云可视化',
    desc: '实时摄像头画面转化为彩色 3D 点云，支持视角切换和数据导出',
    techs: ['Three.js Points', 'WebGL', '点云渲染']
  },
  {
    route: '/camera/gesture-3d',
    icon: '🤏',
    bg: '#fdf2f8, #fce7f3',
    tag: '手势', tagClass: 'tag-pink',
    title: '手势控制 3D 模型控制器',
    desc: '握拳控制位置，开掌控制方向，捏合缩放，左手旋转',
    techs: ['MediaPipe Hands', 'Three.js', '手势识别']
  }
]
</script>

<style scoped>
.top-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 32px;
  background: rgba(250, 249, 247, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #e8e8e8;
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
  font-size: 16px;
}
.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.3px;
}
.page-name {
  font-size: 14px;
  color: #888;
  padding-left: 16px;
  border-left: 1px solid #e0e0e0;
}

.hero {
  text-align: center;
  padding: 48px 20px 36px;
}
.hero h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.5px;
  margin-bottom: 10px;
}
.hero p {
  font-size: 15px;
  color: #888;
  max-width: 500px;
  margin: 0 auto;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px 80px;
}

.card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 16px;
  overflow: hidden;
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
  cursor: pointer;
  display: block;
}
.card:hover {
  transform: translateY(-3px);
  border-color: #c4b5fd;
  box-shadow: 0 8px 32px rgba(124, 58, 237, 0.08);
}

.card-icon {
  height: 130px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 52px;
}
.card-body {
  padding: 20px;
}

.card-tag {
  display: inline-block;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  margin-bottom: 10px;
  font-weight: 500;
}
.tag-green { background: #f0fdf4; color: #16a34a; }
.tag-purple { background: #f5f3ff; color: #7c3aed; }
.tag-orange { background: #fff7ed; color: #ea580c; }
.tag-blue { background: #eff6ff; color: #2563eb; }
.tag-red { background: #fef2f2; color: #dc2626; }
.tag-teal { background: #ecfdf5; color: #0d9488; }
.tag-yellow { background: #fefce8; color: #ca8a04; }
.tag-violet { background: #faf5ff; color: #7c3aed; }
.tag-pink { background: #fdf2f8; color: #db2777; }

.card h3 {
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}
.card p {
  font-size: 13px;
  color: #888;
  line-height: 1.6;
}
.tech {
  margin-top: 12px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tech span {
  font-size: 10px;
  padding: 2px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  color: #888;
}
</style>
