<template>
  <div class="dify-embed-page">
    <iframe
      ref="difyFrame"
      :src="difyUrl"
      class="dify-frame"
      frameborder="0"
      allow="clipboard-read; clipboard-write"
      @load="onLoad"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const difyFrame = ref(null)
const difyUrl = ref('/dify/')

onMounted(() => {
  // Dify 登录后会自动跳转到 apps 页面
})

function onLoad() {
  // 隐藏 Dify 自带的侧边导航，利用我们的导航
  try {
    const iframe = difyFrame.value
    if (iframe && iframe.contentDocument) {
      const style = iframe.contentDocument.createElement('style')
      style.textContent = `
        /* 隐藏 Dify 顶部导航（我们有自己的一级导航） */
        header.h-full, nav.h-full, .ant-layout-sider { display: none !important; }
        main { margin-left: 0 !important; }
      `
      iframe.contentDocument.head.appendChild(style)
    }
  } catch (e) {
    // 跨域无法访问 iframe 内容，忽略
  }
}
</script>

<style scoped>
.dify-embed-page {
  width: 100%; height: calc(100vh - 60px); overflow: hidden;
}
.dify-frame {
  width: 100%; height: 100%; border: none;
}
</style>
