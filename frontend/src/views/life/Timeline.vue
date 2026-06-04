<template>
  <div class="timeline">
    <div class="timeline-header">
      <h4>人生轨迹</h4>
      <span class="stage-badge">{{ currentStageName }}</span>
    </div>
    <div class="timeline-list">
      <div
        v-for="(item, index) in items"
        :key="index"
        class="timeline-item"
        :class="{ active: index === items.length - 1 }"
      >
        <div class="timeline-dot"></div>
        <div class="timeline-content">
          <span class="timeline-tag">{{ item.event_tag }}</span>
          <span class="timeline-stage">{{ item.stage_name }}</span>
        </div>
      </div>
      <div v-if="!items.length" class="timeline-empty">尚未开始</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  currentStageName: { type: String, default: '' },
})
</script>

<style scoped>
.timeline {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
}
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.timeline-header h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}
.stage-badge {
  font-size: 11px;
  color: #7c3aed;
  background: #f5f3ff;
  padding: 2px 8px;
  border-radius: 10px;
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  position: relative;
}
.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 20px;
  bottom: -8px;
  width: 1px;
  background: #e8e8e8;
}
.timeline-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #d1d5db;
  flex-shrink: 0;
  margin-top: 2px;
}
.timeline-item.active .timeline-dot {
  background: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
}
.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.timeline-tag {
  font-size: 12px;
  color: #666;
}
.timeline-stage {
  font-size: 11px;
  color: #aaa;
}
.timeline-empty {
  font-size: 13px;
  color: #ccc;
  text-align: center;
  padding: 16px 0;
}
</style>
