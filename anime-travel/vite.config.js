import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

process.env.NO_PROXY = 'localhost,127.0.0.1'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  server: {
    proxy: {
      '/api/bgm': {
        target: 'https://api.bgm.tv',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/bgm/, ''),
      },
      '/api/anitabi': {
        target: 'https://api.anitabi.cn',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/anitabi/, ''),
      },
      '/api/ors': {
        target: 'https://api.openrouteservice.org',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/ors/, ''),
      },
    },
  },
})
