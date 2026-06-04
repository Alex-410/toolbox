import { ref } from 'vue'

const API_BASE = '/api/life'

export function useLifeSimulator() {
  const sessionId = ref(null)
  const worldType = ref(null)
  const attributes = ref({})
  const background = ref({})
  const story = ref('')
  const options = ref([])
  const stage = ref(0)
  const stageName = ref('')
  const eventTag = ref('')
  const isActive = ref(false)
  const isLoading = ref(false)
  const history = ref([])
  const ending = ref(null)
  const error = ref(null)

  async function startGame(type) {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/start/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ world_type: type }),
      })
      if (!res.ok) throw new Error('启动游戏失败')
      const data = await res.json()
      sessionId.value = data.session_id
      worldType.value = data.world_type
      attributes.value = data.attributes
      background.value = data.background
      story.value = data.story
      options.value = data.options
      stage.value = data.stage
      stageName.value = data.stage_name
      eventTag.value = data.event_tag
      isActive.value = data.is_active
      history.value = [{
        stage: data.stage,
        stage_name: data.stage_name,
        event_tag: data.event_tag,
        story: data.story,
      }]
      ending.value = null
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function makeChoice(choiceId) {
    if (!sessionId.value) return
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/choose/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId.value,
          choice_id: choiceId,
        }),
      })
      if (!res.ok) throw new Error('提交选择失败')
      const data = await res.json()

      attributes.value = data.attributes
      stage.value = data.stage
      stageName.value = data.stage_name
      isActive.value = data.is_active
      history.value = data.history || history.value

      if (!data.is_active) {
        ending.value = {
          ending: data.ending,
          score: data.score,
          title: data.title,
          tags: data.tags,
        }
        story.value = data.ending
        options.value = []
      } else {
        story.value = data.story
        options.value = data.options
        eventTag.value = data.event_tag
        history.value.push({
          stage: data.stage,
          stage_name: data.stage_name,
          event_tag: data.event_tag,
          story: data.story,
        })
      }

      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    sessionId.value = null
    worldType.value = null
    attributes.value = {}
    background.value = {}
    story.value = ''
    options.value = []
    stage.value = 0
    stageName.value = ''
    eventTag.value = ''
    isActive.value = false
    isLoading.value = false
    history.value = []
    ending.value = null
    error.value = null
  }

  return {
    sessionId, worldType, attributes, background,
    story, options, stage, stageName, eventTag,
    isActive, isLoading, history, ending, error,
    startGame, makeChoice, reset,
  }
}
