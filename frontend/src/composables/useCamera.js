import { ref, onUnmounted } from 'vue'

const VIRTUAL_KEYWORDS = [
  'obs', 'virtual', 'vcam', 'splitcam', 'manycam',
  'snap camera', 'xsplit', 'elgato', 'streamlabs', 'ndi'
]

let allCameras = []
let selectedDeviceId = null
let userManuallySelected = false

async function refreshCameraList(select) {
  const devices = await navigator.mediaDevices.enumerateDevices()
  allCameras = devices.filter(d => d.kind === 'videoinput')

  select.innerHTML = ''

  if (allCameras.length === 0) {
    select.innerHTML = '<option value="">未检测到摄像头</option>'
    return
  }

  const hasLabels = allCameras.some(cam => cam.label && cam.label.length > 0)

  const physical = []
  const virtual = []
  const unlabeled = []

  allCameras.forEach(cam => {
    const label = cam.label || ''
    const lower = label.toLowerCase()
    if (!label) {
      unlabeled.push(cam)
    } else if (VIRTUAL_KEYWORDS.some(k => lower.includes(k))) {
      virtual.push(cam)
    } else {
      physical.push(cam)
    }
  })

  if (physical.length > 0) {
    const group = document.createElement('optgroup')
    group.label = '实体摄像头'
    physical.forEach((cam, i) => {
      const opt = document.createElement('option')
      opt.value = cam.deviceId
      opt.textContent = cam.label || `摄像头 ${i + 1}`
      group.appendChild(opt)
    })
    select.appendChild(group)
  }

  if (virtual.length > 0) {
    const group = document.createElement('optgroup')
    group.label = '虚拟摄像头'
    virtual.forEach((cam, i) => {
      const opt = document.createElement('option')
      opt.value = cam.deviceId
      opt.textContent = cam.label || `虚拟摄像头 ${i + 1}`
      group.appendChild(opt)
    })
    select.appendChild(group)
  }

  if (unlabeled.length > 0) {
    const group = document.createElement('optgroup')
    group.label = '其他摄像头'
    unlabeled.forEach((cam, i) => {
      const opt = document.createElement('option')
      opt.value = cam.deviceId
      opt.textContent = `摄像头 ${i + 1}`
      group.appendChild(opt)
    })
    select.appendChild(group)
  }

  if (!userManuallySelected) {
    if (physical.length > 0) {
      selectedDeviceId = physical[0].deviceId
    } else if (allCameras.length > 0) {
      selectedDeviceId = allCameras[0].deviceId
    }
  } else if (hasLabels) {
    const currentIsVirtual = virtual.some(cam => cam.deviceId === selectedDeviceId)
    if (currentIsVirtual && physical.length > 0) {
      selectedDeviceId = physical[0].deviceId
    }
  }

  if (selectedDeviceId) {
    select.value = selectedDeviceId
  }
}

function initCameraSelector(container, onChange) {
  const existing = container.querySelector(`select[id^="cameraSelect"]`)
  if (existing) {
    existing.remove()
  }

  const wrapper = document.createElement('div')
  wrapper.className = 'camera-selector-wrapper'

  const label = document.createElement('label')
  label.textContent = '摄像头选择'
  label.style.cssText = 'font-size:12px;color:#aaa;margin-bottom:4px;display:block;'

  const select = document.createElement('select')
  select.id = `cameraSelect_${Date.now()}`
  select.style.cssText = 'width:100%;background:#1e1e1e;border:1px solid #333;border-radius:6px;color:#e0e0e0;padding:6px 8px;font-size:12px;cursor:pointer;'
  select.innerHTML = '<option value="">加载中...</option>'

  wrapper.appendChild(label)
  wrapper.appendChild(select)
  container.appendChild(wrapper)

  select.addEventListener('change', async () => {
    selectedDeviceId = select.value
    userManuallySelected = true
    if (onChange) {
      try {
        await onChange(selectedDeviceId)
      } catch (e) {
        console.error('切换摄像头回调错误:', e)
      }
    }
  })

  navigator.mediaDevices.enumerateDevices().then(devices => {
    const cameras = devices.filter(d => d.kind === 'videoinput')
    const hasLabels = cameras.some(c => c.label && c.label.length > 0)
    if (!hasLabels) {
      navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
        .then(tempStream => {
          tempStream.getTracks().forEach(t => t.stop())
          return refreshCameraList(select)
        })
        .catch(err => {
          console.warn('获取摄像头权限失败:', err)
          refreshCameraList(select)
        })
    } else {
      refreshCameraList(select)
    }
  })
}

async function getSelectedStream(constraints = {}) {
  const labelsKnown = allCameras.some(cam => cam.label && cam.label.length > 0)

  if (!labelsKnown) {
    const tempStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    })
    tempStream.getTracks().forEach(t => t.stop())

    const select = document.querySelector('select[id^="cameraSelect"]')
    if (select) await refreshCameraList(select)
  }

  const videoConstraints = selectedDeviceId
    ? { deviceId: { exact: selectedDeviceId } }
    : { facingMode: 'user' }

  const finalConstraints = {
    video: { ...videoConstraints, width: { ideal: 1280 }, height: { ideal: 720 }, ...constraints },
    audio: false
  }

  const stream = await navigator.mediaDevices.getUserMedia(finalConstraints)

  setTimeout(() => {
    const select = document.querySelector('select[id^="cameraSelect"]')
    if (select) refreshCameraList(select)
  }, 500)

  return stream
}

export function useCamera() {
  const stream = ref(null)
  const isRunning = ref(false)

  const startCamera = async (videoEl, constraints = {}) => {
    try {
      stream.value = await getSelectedStream(constraints)
      videoEl.srcObject = stream.value
      await new Promise((resolve, reject) => {
        videoEl.onloadedmetadata = () => videoEl.play().then(resolve).catch(reject)
        videoEl.onerror = reject
        setTimeout(() => reject(new Error('视频加载超时')), 10000)
      })
      isRunning.value = true
      return stream.value
    } catch (e) {
      console.error('启动摄像头失败:', e)
      throw e
    }
  }

  const stopCamera = () => {
    if (stream.value) {
      stream.value.getTracks().forEach(t => t.stop())
      stream.value = null
    }
    isRunning.value = false
  }

  onUnmounted(() => {
    stopCamera()
  })

  return {
    stream,
    isRunning,
    startCamera,
    stopCamera,
    initCameraSelector,
    getSelectedStream
  }
}
