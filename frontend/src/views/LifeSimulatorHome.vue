<template>
  <div class="life-home">
    <header class="top-bar">
      <router-link to="/" class="logo">
        <span class="logo-icon">✦</span>
        <span class="logo-text">工具集</span>
      </router-link>
      <span class="page-name">人生模拟器</span>
    </header>

    <main class="content">
      <section class="hero">
        <h1>人生模拟器</h1>
        <p>选择你的世界观，开启一段全新的人生旅程。每一次选择，都将导向不同的命运。</p>
      </section>

      <div class="world-grid">
        <div
          v-for="world in worlds"
          :key="world.type"
          class="world-card"
          @click="selectWorld(world.type)"
        >
          <div class="world-icon">{{ world.icon }}</div>
          <h3>{{ world.title }}</h3>
          <p>{{ world.desc }}</p>
          <div class="world-tags">
            <span v-for="tag in world.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const worlds = [
  {
    type: 'modern',
    icon: '🏙️',
    title: '现代都市',
    desc: '在钢筋水泥的丛林中书写你的人生故事。升学、职场、创业、家庭……每一个选择都影响着命运的走向。',
    tags: ['职场', '创业', '社交', '家庭'],
  },
  {
    type: 'ancient',
    icon: '⚔️',
    title: '古代江湖',
    desc: '穿越到刀光剑影的武侠世界。拜师学艺、行走江湖、门派纷争、武林大会……你的剑，指向何方？',
    tags: ['修仙', '武侠', '江湖', '门派'],
  },
  {
    type: 'future',
    icon: '🚀',
    title: '未来科幻',
    desc: '踏入星际纪元的浩瀚宇宙。基因改造、AI共生、星际殖民、文明冲突……人类的未来，由你定义。',
    tags: ['星际', 'AI', '基因', '探索'],
  },
]

function selectWorld(type) {
  router.push({ path: '/life/game', query: { world: type } })
}
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
  font-weight: 600;
  color: #1a1a1a;
}
.page-name {
  font-size: 14px;
  color: #888;
  padding-left: 16px;
  border-left: 1px solid #e0e0e0;
}

.content {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 32px;
}
.hero {
  text-align: center;
  padding: 72px 0 48px;
}
.hero h1 {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.5px;
  margin-bottom: 12px;
}
.hero p {
  font-size: 15px;
  color: #888;
  max-width: 480px;
  margin: 0 auto;
  line-height: 1.7;
}

.world-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  padding-bottom: 80px;
}
.world-card {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.world-card:hover {
  border-color: #c4b5fd;
  box-shadow: 0 8px 32px rgba(124, 58, 237, 0.08);
  transform: translateY(-3px);
}
.world-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.world-card h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 10px;
}
.world-card p {
  font-size: 13px;
  color: #888;
  line-height: 1.7;
  margin-bottom: 16px;
}
.world-tags {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}
.world-tags span {
  font-size: 11px;
  padding: 3px 10px;
  background: #f5f3ff;
  color: #7c3aed;
  border-radius: 20px;
}

@media (max-width: 768px) {
  .world-grid {
    grid-template-columns: 1fr;
  }
}
</style>
