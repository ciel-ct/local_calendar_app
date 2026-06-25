import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Viteに「Vueファイルをちゃんと翻訳してね！」って指示する設定ですファイル
export default defineConfig({
  plugins: [vue()],
  server: {
    // Docker内でも確実にファイル変更を検知する設定です
    watch: {
      usePolling: true, 
    },
  },
})