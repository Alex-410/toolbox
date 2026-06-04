import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/ToolboxHome.vue')
  },
  {
    path: '/life',
    name: 'LifeSimulator',
    component: () => import('../views/LifeSimulatorHome.vue')
  },
  {
    path: '/life/game',
    name: 'LifeGame',
    component: () => import('../views/life/LifeSimulatorGame.vue')
  },
  {
    path: '/camera',
    name: 'Camera',
    component: () => import('../views/CameraHome.vue')
  },
  {
    path: '/camera/ar-background',
    name: 'ArBackground',
    component: () => import('../views/tools/ToolArBackground.vue')
  },
  {
    path: '/camera/face-sticker',
    name: 'FaceSticker',
    component: () => import('../views/tools/ToolFaceSticker.vue')
  },
  {
    path: '/camera/pose-skeleton',
    name: 'PoseSkeleton',
    component: () => import('../views/tools/ToolPoseSkeleton.vue')
  },
  {
    path: '/camera/particle-art',
    name: 'ParticleArt',
    component: () => import('../views/tools/ToolParticleArt.vue')
  },
  {
    path: '/camera/camera-game',
    name: 'CameraGame',
    component: () => import('../views/tools/ToolCameraGame.vue')
  },
  {
    path: '/camera/distortion',
    name: 'Distortion',
    component: () => import('../views/tools/ToolDistortion.vue')
  },
  {
    path: '/camera/webxr-ar',
    name: 'WebxrAr',
    component: () => import('../views/tools/ToolWebxrAr.vue')
  },
  {
    path: '/camera/point-cloud',
    name: 'PointCloud',
    component: () => import('../views/tools/ToolPointCloud.vue')
  },
  {
    path: '/camera/gesture-3d',
    name: 'Gesture3d',
    component: () => import('../views/tools/ToolGesture3d.vue')
  },
  {
    path: '/tools',
    name: 'Tools',
    component: () => import('../views/tools/ToolsHome.vue')
  },
  {
    path: '/tools/qrcode',
    name: 'QrCode',
    component: () => import('../views/tools/ToolQrCode.vue')
  },
  {
    path: '/tools/base64',
    name: 'Base64',
    component: () => import('../views/tools/ToolBase64.vue')
  },
  {
    path: '/tools/image',
    name: 'ImageTool',
    component: () => import('../views/tools/ToolImage.vue')
  },
  {
    path: '/tools/pdf',
    name: 'PdfTool',
    component: () => import('../views/tools/ToolPdf.vue')
  },
  {
    path: '/anime-travel',
    name: 'AnimeTravelLoading',
    component: () => import('../views/AnimeTravelLoading.vue')
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
