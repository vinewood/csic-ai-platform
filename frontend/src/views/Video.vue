<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1574375927938-d5a98e922061?w=1200&q=80);">
      <div class="hero-content">
        <h2>视频分析</h2>
        <p>上传 · 转录 · 摘要 · 知识闪卡</p>
      </div>
    </div>

    <div class="video-split">
      <!-- 左侧：上传 + 设置 -->
      <div class="video-left">
        <el-card shadow="never" class="video-card">
          <template #header><span style="font-weight:600;">上传文件</span></template>
          <el-upload drag class="upload-zone" :auto-upload="false">
            <el-icon :size="36" color="#1677ff"><UploadFilled /></el-icon>
            <p style="font-size:13px;margin:8px 0 4px;">拖拽或点击上传</p>
            <p style="font-size:11px;color:#94a3b8;">MP4, AVI, MP3, WAV</p>
          </el-upload>
          <el-input v-model="link" placeholder="或粘贴在线链接..." style="margin-top:10px;" size="default" />
          <el-button type="primary" @click="start" :loading="analyzing" style="width:100%;margin-top:12px;">开始分析</el-button>
        </el-card>

        <el-card shadow="never" class="video-card" style="margin-top:10px;">
          <template #header><span style="font-weight:600;">分析设置</span></template>
          <el-checkbox v-model="genSummary" label="生成AI摘要" size="default" />
          <el-checkbox v-model="genFlashcards" label="生成知识闪卡" size="default" style="margin-left:16px;" />
          <el-checkbox v-model="genMindmap" label="生成思维导图" size="default" style="margin-left:16px;" />
        </el-card>
      </div>

      <!-- 右侧：结果 -->
      <div class="video-right">
        <el-card shadow="never" class="video-card">
          <template #header><span style="font-weight:600;">分析结果</span></template>
          <div v-if="!done" class="result-empty">
            <el-icon :size="40" color="#d1d5db"><VideoCamera /></el-icon>
            <p>上传文件后开始分析</p>
          </div>
          <template v-else>
            <el-tabs v-model="resultTab">
              <el-tab-pane label="全文转录" name="transcript">
                <div class="result-text">{{ result?.transcript }}</div>
              </el-tab-pane>
              <el-tab-pane label="AI摘要" name="summary">
                <div class="result-text">{{ result?.summary }}</div>
              </el-tab-pane>
              <el-tab-pane label="知识闪卡" name="flashcards">
                <div v-for="(fc, i) in result?.flashcards || []" :key="i" class="flashcard">
                  <strong>{{ fc.q }}</strong>
                  <p>{{ fc.a }}</p>
                </div>
              </el-tab-pane>
              <el-tab-pane label="思维导图" name="mindmap">
                <div class="mindmap-wrap">
                  <div class="mindmap-hint" v-if="!showMindmap">点击下方按钮生成思维导图</div>
                  <div id="mindmap-container" class="mindmap-container" v-show="showMindmap"></div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </template>
        </el-card>

        <div v-if="done" style="margin-top:10px;display:flex;gap:8px;">
          <el-button size="small" :icon="Download" @click="exportResult">导出文本</el-button>
          <el-button size="small" :icon="Share" @click="shareResult">分享</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, VideoCamera, Download, Share } from '@element-plus/icons-vue'
import { apiGet, apiPost, apiDelete, apiUpload } from '../api.js'

const link = ref('')
const analyzing = ref(false)
const done = ref(false)
const genSummary = ref(true)
const genFlashcards = ref(true)
const genMindmap = ref(true)
const showMindmap = ref(false)
const resultTab = ref('transcript')
const result = ref(null)
const tasks = ref([])

onMounted(async () => {
  try {
    const res = await apiGet('/api/video')
    tasks.value = (res && res.tasks) ? res.tasks : (Array.isArray(res) ? res : [])
  } catch (e) {
    // 静默，任务列表为可选数据
  }
})

async function start() {
  const fileInput = document.querySelector('.el-upload input[type="file"]')
  const file = fileInput?.files?.[0]

  if (!file && !link.value) {
    ElMessage.warning('请选择文件或输入链接')
    return
  }

  analyzing.value = true

  try {
    let id
    if (file) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('summary', String(genSummary.value))
      formData.append('flashcards', String(genFlashcards.value))
      formData.append('mindmap', String(genMindmap.value))

      const res = await apiUpload('/api/video/upload', formData)
      id = res.id
    } else {
      const res = await apiPost('/api/video/upload', {
        url: link.value,
        summary: genSummary.value,
        flashcards: genFlashcards.value,
        mindmap: genMindmap.value
      })
      id = res.id
    }

    pollResult(id)
  } catch (e) {
    ElMessage.error('上传失败: ' + (e.message || '未知错误'))
    analyzing.value = false
  }
}

async function pollResult(id) {
  let retries = 0
  const maxRetries = 60

  const poll = async () => {
    try {
      const res = await apiGet(`/api/video/${id}`)
      if (res.status === 'done') {
        result.value = {
          transcript: res.transcript || '',
          summary: res.summary || '',
          flashcards: res.flashcards || []
        }
        done.value = true
        analyzing.value = false

        if (genMindmap.value && res.mindmap) {
          showMindmap.value = true
          const container = document.getElementById('mindmap-container')
          if (container) {
            container.innerHTML = ''
            renderSimpleMindmap(container, res.mindmap)
          }
        }
      } else if (res.status === 'error') {
        ElMessage.error('分析失败: ' + (res.error || '未知错误'))
        analyzing.value = false
      } else if (retries < maxRetries) {
        retries++
        setTimeout(poll, 2000)
      } else {
        ElMessage.error('分析超时')
        analyzing.value = false
      }
    } catch (e) {
      if (retries < maxRetries) {
        retries++
        setTimeout(poll, 2000)
      } else {
        ElMessage.error('查询结果超时: ' + (e.message || '未知错误'))
        analyzing.value = false
      }
    }
  }

  setTimeout(poll, 2000)
}

// 导出：纯前端生成 Markdown 下载，不依赖后端 /api/video/export（该路由不存在）
function exportResult() {
  if (!result.value) return
  try {
    const r = result.value
    let md = '# 视频解析结果\n\n'
    if (r.summary) md += `## AI 摘要\n\n${r.summary}\n\n`
    if (r.transcript) md += `## 逐字稿\n\n${r.transcript}\n\n`
    if (r.flashcards && r.flashcards.length) {
      md += '## 记忆卡片\n\n'
      r.flashcards.forEach((c, i) => {
        md += `${i + 1}. **${c.question || c.front || ''}**\n   ${c.answer || c.back || ''}\n\n`
      })
    }
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `视频解析_${new Date().toISOString().slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(a.href)
    ElMessage.success('已导出 Markdown 文件')
  } catch (e) {
    ElMessage.error('导出失败：' + (e.message || '未知错误'))
  }
}

// 分享：复制当前页面链接到剪贴板，不依赖后端 /api/video/share（该路由不存在）
async function shareResult() {
  if (!result.value) return
  const link = window.location.href
  try {
    await navigator.clipboard.writeText(link)
    ElMessage.success('页面链接已复制到剪贴板')
  } catch {
    // 剪贴板 API 不可用（非 HTTPS 等场景）时降级为选中文本
    const ta = document.createElement('textarea')
    ta.value = link
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    if (ok) ElMessage.success('页面链接已复制到剪贴板')
    else ElMessage.warning('复制失败，请手动复制地址栏链接')
  }
}

function renderSimpleMindmap(container, tree) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', '100%')
  svg.setAttribute('height', '320')
  svg.style.display = 'block'
  const w = container.clientWidth || 600, h = 320, cx = 40, cy = h / 2
  const colors = ['#1677ff', '#10b981', '#f59e0b']
  
  // 根节点
  let root = document.createElementNS('http://www.w3.org/2000/svg', 'text')
  root.setAttribute('x', cx); root.setAttribute('y', cy)
  root.setAttribute('fill', '#1677ff'); root.setAttribute('font-size', '16')
  root.setAttribute('font-weight', 'bold')
  root.textContent = tree.data.text
  svg.appendChild(root)

  // 子节点
  const childX = cx + 160
  const spacing = h / (tree.data.children.length + 1)
  tree.data.children.forEach((child, i) => {
    const childY = spacing * (i + 1)
    // 连线
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    line.setAttribute('x1', cx + 80); line.setAttribute('y1', cy)
    line.setAttribute('x2', childX); line.setAttribute('y2', childY)
    line.setAttribute('stroke', colors[i]); line.setAttribute('stroke-width', '2')
    svg.appendChild(line)

    // 子节点文字
    let text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    text.setAttribute('x', childX + 10); text.setAttribute('y', childY + 4)
    text.setAttribute('fill', colors[i]); text.setAttribute('font-size', '14')
    text.setAttribute('font-weight', '600')
    text.textContent = child.text
    svg.appendChild(text)

    // 孙节点
    if (child.children) {
      const gX = childX + 140
      child.children.forEach((gc, j) => {
        const gY = childY - 24 + j * 24
        const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line')
        line2.setAttribute('x1', childX + 60); line2.setAttribute('y1', childY)
        line2.setAttribute('x2', gX); line2.setAttribute('y2', gY)
        line2.setAttribute('stroke', '#d1d5db'); line2.setAttribute('stroke-width', '1')
        svg.appendChild(line2)

        let gt = document.createElementNS('http://www.w3.org/2000/svg', 'text')
        gt.setAttribute('x', gX + 8); gt.setAttribute('y', gY + 3)
        gt.setAttribute('fill', '#4b5563'); gt.setAttribute('font-size', '12')
        gt.textContent = gc.text
        svg.appendChild(gt)
      })
    }
  })
  container.appendChild(svg)
}
</script>

<style scoped>
.video-split {
  display: flex;
  gap: 12px;
  min-height: 0;
}
.video-left { width: 340px; flex-shrink: 0; }
.video-right { flex: 1; min-width: 0; }
.video-card { border-radius: 8px; border: 1px solid var(--border-color); }

.upload-zone :deep(.el-upload-dragger) {
  width: 100%; padding: 24px 16px; border-radius: 8px;
}

.result-empty {
  text-align: center; padding: 48px 0; color: #94a3b8;
}
.result-empty p { margin-top: 10px; }

.result-text {
  padding: 14px; background: #f8fafc; border-radius: 6px;
  white-space: pre-wrap; line-height: 1.7; font-size: 13px;
  max-height: 320px; overflow-y: auto;
}
.flashcard {
  padding: 12px 14px; background: #f8fafc; border-radius: 6px;
  margin-bottom: 8px; border-left: 3px solid #13c2c2;
}
.flashcard strong { font-size: 13px; }
.flashcard p { margin: 6px 0 0; font-size: 13px; color: var(--text-secondary); }

.mindmap-wrap { min-height: 200px; }
.mindmap-hint { text-align: center; padding: 60px 0; color: #94a3b8; font-size: 14px; }
.mindmap-container { width: 100%; overflow-x: auto; }
.mindmap-container svg { min-width: 500px; }

@media (max-width: 768px) {
  .video-split { flex-direction: column; }
  .video-left { width: 100%; }
}
</style>
