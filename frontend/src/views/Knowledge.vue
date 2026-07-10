<template>
  <div class="dify-embed-page">
    <iframe
      :src="difyUrl"
      class="dify-frame"
      frameborder="0"
      allow="clipboard-read; clipboard-write"
    />
  </div>
</template>

<script setup>
const difyUrl = '/dify/datasets'
</script>

<style scoped>
.dify-embed-page {
  width: 100%; height: calc(100vh - 60px); overflow: hidden;
}
.dify-frame {
  width: 100%; height: 100%; border: none;
}
</style>
