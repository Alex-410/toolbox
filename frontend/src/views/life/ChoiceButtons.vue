<template>
  <div class="choices" :class="{ locked: !unlocked }">
    <button
      v-for="opt in options"
      :key="opt.id"
      class="choice-btn"
      :class="{ selected: selectedId === opt.id }"
      :disabled="!unlocked"
      @click="select(opt.id)"
    >
      <span class="choice-label">{{ opt.text }}</span>
    </button>
    <div v-if="!unlocked && options.length" class="lock-hint">
      <span class="lock-icon">⏳</span> 剧情进行中…
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  options: { type: Array, default: () => [] },
  unlocked: { type: Boolean, default: false },
})

const emit = defineEmits(['choose'])
const selectedId = ref(null)

function select(id) {
  selectedId.value = id
  emit('choose', id)
}
</script>

<style scoped>
.choices {
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: opacity 0.3s;
}
.choices.locked {
  opacity: 0.5;
  pointer-events: none;
}
.choice-btn {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 14px 20px;
  text-align: left;
  font-size: 14px;
  color: #333;
  transition: all 0.2s ease;
  cursor: pointer;
  line-height: 1.5;
}
.choice-btn:hover:not(:disabled) {
  border-color: #c4b5fd;
  background: #faf8ff;
  color: #7c3aed;
}
.choice-btn.selected {
  border-color: #7c3aed;
  background: #f5f3ff;
  color: #7c3aed;
}
.choice-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
.choice-label {
  font-weight: 500;
}
.lock-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #bbb;
  padding: 8px 0;
}
.lock-icon {
  font-size: 14px;
}
</style>
