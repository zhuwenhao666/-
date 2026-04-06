import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd())
  return {
    plugins: [vue()],
    server: {
      port: 3085,
      proxy: {
        '/fastAPIbackend': {
          target: env.VITE_FASTAPI_BACKEN_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/fastAPIbackend/, '')
        }
      }
    },
    resolve: {
      alias: {
        'cesium': path.resolve(__dirname, './src/Cesium'), // 指向本地cesium库
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        '#': fileURLToPath(new URL('./public', import.meta.url))
      }
    },
  }
})
