<template>
  <div class="attr-panel">
    <div class="panel-header">
      <h3>{{ bg.family }}</h3>
      <span class="talent">{{ bg.talent }}</span>
    </div>

    <div class="attrs">
      <div v-for="attr in attrList" :key="attr.key" class="attr-row">
        <span class="attr-label">{{ attr.label }}</span>
        <div class="attr-bar">
          <div class="attr-fill" :style="{ width: attr.value + '%', background: attr.color }"></div>
        </div>
        <span class="attr-value">{{ attr.value }}</span>
      </div>
    </div>

    <div class="meta">
      <div class="meta-item">
        <span class="meta-label">性格</span>
        <span class="meta-value">{{ bg.personality }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  attributes: { type: Object, default: () => ({}) },
  background: { type: Object, default: () => ({}) },
})

const bg = computed(() => props.background)

const attrList = computed(() => [
  { key: 'intelligence', label: '智力', value: props.attributes.intelligence || 0, color: '#7c3aed' },
  { key: 'charm', label: '魅力', value: props.attributes.charm || 0, color: '#ec4899' },
  { key: 'strength', label: '体质', value: props.attributes.strength || 0, color: '#f59e0b' },
  { key: 'luck', label: '运气', value: props.attributes.luck || 0, color: '#10b981' },
  { key: 'wealth', label: '财富', value: props.attributes.wealth || 0, color: '#3b82f6' },
])
</script>

<style scoped>
.attr-panel {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
}
.panel-header {
  margin-bottom: 20px;
}
.panel-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 6px;
}
.talent {
  font-size: 12px;
  color: #7c3aed;
  background: #f5f3ff;
  padding: 2px 8px;
  border-radius: 10px;
}

.attrs {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.attr-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.attr-label {
  font-size: 12px;
  color: #888;
  width: 32px;
  flex-shrink: 0;
}
.attr-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}
.attr-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.attr-value {
  font-size: 12px;
  color: #666;
  width: 24px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.meta {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.meta-label {
  font-size: 12px;
  color: #999;
}
.meta-value {
  font-size: 13px;
  color: #555;
}
</style>
