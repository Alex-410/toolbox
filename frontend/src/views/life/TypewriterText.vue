<template>
  <div class="typewriter-wrap">
    <div class="typewriter-text" v-html="displayedText"></div>
    <span v-if="isTyping" class="cursor">|</span>
    <button v-if="isTyping" class="skip-btn" @click="skip">跳过</button>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  speed: { type: Number, default: 50 },
})

const emit = defineEmits(['complete'])

const displayedText = ref('')
const isTyping = ref(false)
let timer = null
let currentIndex = 0

function startTyping() {
  stopTyping()
  displayedText.value = ''
  currentIndex = 0
  isTyping.value = true
  typeNext()
}

function typeNext() {
  if (currentIndex >= props.text.length) {
    isTyping.value = false
    emit('complete')
    return
  }

  const char = props.text[currentIndex]
  if (char === '\n') {
    displayedText.value += '<br>'
  } else {
    displayedText.value += char
  }
  currentIndex++

  let delay = props.speed
  if ('，。！？、；：'.includes(char)) {
    delay = props.speed * 4
  } else if ('，.!?:;'.includes(char)) {
    delay = props.speed * 3
  }

  timer = setTimeout(typeNext, delay)
}

function skip() {
  stopTyping()
  displayedText.value = props.text.replace(/\n/g, '<br>')
  isTyping.value = false
  emit('complete')
}

function stopTyping() {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
}

watch(() => props.text, (newText) => {
  if (newText) {
    startTyping()
  }
}, { immediate: true })

onBeforeUnmount(() => {
  stopTyping()
})

defineExpose({ skip, isTyping })
</script>

<style scoped>
.typewriter-wrap {
  position: relative;
}
.typewriter-text {
  font-size: 15px;
  line-height: 1.9;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor {
  display: inline-block;
  color: #7c3aed;
  font-weight: 300;
  animation: blink 0.8s infinite;
  margin-left: 1px;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
.skip-btn {
  position: absolute;
  top: -32px;
  right: 0;
  font-size: 12px;
  color: #999;
  background: none;
  padding: 4px 10px;
  border-radius: 6px;
  transition: all 0.15s;
}
.skip-btn:hover {
  color: #7c3aed;
  background: #f5f3ff;
}
</style>
