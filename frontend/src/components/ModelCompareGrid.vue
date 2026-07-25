<template>
  <div class="mcmp-wrap">
    <!-- 最大化态：单区块全屏聚焦 -->
    <div v-if="maximized!==null" class="pane pane-max">
      <div class="pane-header">
        <span class="model-dot" :style="{background:modelColor(panes[maximized].model)}"></span>
        <span class="pane-model-name">{{ modelLabel(panes[maximized].model) }}</span>
        <span v-if="panes[maximized].streaming" class="pane-status">回答中…</span>
        <el-button link size="small" title="还原到宫格" @click="maximized=null">
          <el-icon><ZoomOut /></el-icon>
        </el-button>
      </div>
      <div class="pane-body" :ref="el => setPaneRef(el, maximized)">
        <div v-for="(m,i) in panes[maximized].msgs" :key="i" :class="['msg',m.role]">
          <div class="msg-text" :class="{streaming: panes[maximized].streaming && i===panes[maximized].msgs.length-1 && m.role==='assistant'}"
               v-html="render(m.content)"></div>
        </div>
        <div v-if="!panes[maximized].msgs.length" class="pane-empty">在下方输入问题，{{ modelLabel(panes[maximized].model) }} 将在此作答</div>
      </div>
    </div>

    <!-- 宫格态：2/4/6 宫格 -->
    <div v-else class="pane-grid" :style="gridStyle">
      <div v-for="(p,pi) in panes" :key="p.model" class="pane">
        <div class="pane-header">
          <span class="model-dot" :style="{background:modelColor(p.model)}"></span>
          <span class="pane-model-name">{{ modelLabel(p.model) }}</span>
          <span v-if="p.streaming" class="pane-status">回答中…</span>
          <el-button link size="small" title="最大化" @click="maximized=pi">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
        </div>
        <div class="pane-body" :ref="el => setPaneRef(el, pi)">
          <div v-for="(m,i) in p.msgs" :key="i" :class="['msg',m.role]">
            <div class="msg-text" :class="{streaming: p.streaming && i===p.msgs.length-1 && m.role==='assistant'}"
                 v-html="render(m.content)"></div>
          </div>
          <div v-if="!p.msgs.length" class="pane-empty">等待提问…</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 多模型对比宫格工作台（共享组件）
 * - 2/4/6 宫格布局（gridMode 由父级工具栏切换）
 * - 每个模型一个独立区块，可最大化全屏聚焦、可还原原位
 * - 同一问题并行流式发送；首发请求先建立会话，拿到 conversation_id 后
 *   再并发其余请求，避免多请求各自新建会话（meta 事件回传父级）
 * 使用：const gridRef = ref(); gridRef.value.broadcast(query)
 */
import { ref, computed, watch, nextTick } from 'vue'
import { ZoomIn, ZoomOut } from '@element-plus/icons-vue'
import { marked } from 'marked'

const props = defineProps({
  models: { type: Array, default: () => [] },        // 模型 key 数组
  gridMode: { type: String, default: 'grid4' },      // grid2 / grid4 / grid6
  endpoint: { type: String, default: '/api/chat/dify-chat' },
  getConvId: { type: Function, default: () => '' },  // 父级会话 id getter
  extraFn: { type: Function, default: () => ({}) },  // 附加请求字段（skill_id 等）
})
const emit = defineEmits(['meta', 'busy'])

const GRID_DEFS = {
  grid2: { cols: 2, rows: 1 },
  grid4: { cols: 2, rows: 2 },
  grid6: { cols: 3, rows: 2 },
}
const gridStyle = computed(() => {
  const g = GRID_DEFS[props.gridMode] || GRID_DEFS.grid4
  return {
    'grid-template-columns': `repeat(${g.cols}, 1fr)`,
    'grid-template-rows': `repeat(${g.rows}, 1fr)`,
    'grid-auto-rows': '1fr',
  }
})

const MODEL_META = {
  deepseek:      { label: 'DeepSeek V4 Pro', color: '#4D6BFE' },
  qwen:          { label: '通义千问', color: '#615CED' },
  'qwen-plus':   { label: 'Qwen Plus', color: '#615CED' },
  'qwen-max':    { label: 'Qwen Max', color: '#4338CA' },
  'qwen-turbo':  { label: 'Qwen Turbo', color: '#818CF8' },
  'qwen-coder-plus': { label: 'Qwen Coder', color: '#3730A3' },
  'glm-4':       { label: 'GLM', color: '#3B9CFF' },
  zhipu:         { label: '智谱GLM', color: '#3B9CFF' },
  kimi:          { label: 'Kimi', color: '#111827' },
  minimax:       { label: 'MiniMax', color: '#F59E0B' },
  doubao:        { label: '豆包', color: '#22C55E' },
}
const modelLabel = m => MODEL_META[m]?.label || m
const modelColor = m => MODEL_META[m]?.color || '#1677ff'

const panes = ref([])
const maximized = ref(null)
const paneRefs = ref({})

// 模型选择变化 → 同步区块（保留已有区块的对话）
watch(() => props.models, (list) => {
  panes.value = list.map(m => {
    const old = panes.value.find(p => p.model === m)
    return old || { model: m, msgs: [], streaming: false }
  })
  if (maximized.value !== null && maximized.value >= panes.value.length) maximized.value = null
}, { immediate: true, deep: true })

function setPaneRef(el, i) { if (el) paneRefs.value[i] = el }
function scrollPane(i) {
  nextTick(() => { const el = paneRefs.value[i]; if (el) el.scrollTop = el.scrollHeight })
}

function render(t) {
  if (!t) return ''
  try { return marked.parse(t.replace(/\n{3,}/g, '\n\n')) } catch { return t }
}

function clear() { panes.value.forEach(p => { p.msgs = []; p.streaming = false }); maximized.value = null }

/** 广播同一问题到全部区块（并行流式） */
async function broadcast(query) {
  if (!panes.value.length || !query?.trim()) return
  panes.value.forEach(p => {
    p.msgs.push({ role: 'user', content: query.trim() })
    p.msgs.push({ role: 'assistant', content: '' })
    p.streaming = true
  })
  panes.value.forEach((_, i) => scrollPane(i))
  emit('busy', true)

  // 首发：先建立/确认会话，拿到 conversation_id 后再并发其余
  const first = panes.value[0]
  let metaResolve
  const metaPromise = new Promise(r => { metaResolve = r })
  const firstDone = streamOne(query.trim(), first, props.getConvId(), metaResolve)
  const newConvId = await Promise.race([
    metaPromise,
    new Promise(r => setTimeout(() => r(null), 5000)),   // 5s 兜底，不阻塞其余模型
  ])
  if (newConvId) emit('meta', newConvId)

  await Promise.all([
    firstDone,
    ...panes.value.slice(1).map(p => streamOne(query.trim(), p, newConvId || props.getConvId(), null)),
  ])
  emit('busy', false)
}

async function streamOne(query, pane, convId, onMeta) {
  const token = localStorage.getItem('csic_token')
  const API_BASE = window.location.port === '5173' ? 'http://localhost:8000' : ''
  const target = pane.msgs[pane.msgs.length - 1]
  const pi = panes.value.indexOf(pane)
  try {
    const resp = await fetch(`${API_BASE}${props.endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        query, model: pane.model,
        conversation_id: convId === 'new' ? '' : (convId || ''),
        ...props.extraFn(),
      })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let full = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      for (const line of decoder.decode(value, { stream: true }).split('\n')) {
        if (!line.startsWith('data: ')) continue
        const d = line.slice(6)
        if (d === '[DONE]') continue
        try {
          const j = JSON.parse(d)
          if (j.conversation_id && onMeta) onMeta(j.conversation_id)
          if (j.content) { full += j.content; target.content = full; scrollPane(pi) }
        } catch { /* 半包忽略 */ }
      }
    }
  } catch (e) {
    target.content = `[错误] ${e.message}`
  } finally {
    pane.streaming = false
    scrollPane(pi)
  }
}

defineExpose({ broadcast, clear, panes })
</script>

<style scoped>
.mcmp-wrap { height: 100%; min-height: 0; }

/* ===== 宫格 ===== */
.pane-grid { display:grid; gap:10px; height:100%; }
.pane { background:#fff; border:1px solid #e8eaee; border-radius:12px; display:flex; flex-direction:column; min-height:0; overflow:hidden; box-shadow:0 1px 3px rgba(16,24,40,.05); }
.pane-max { height:100%; }
.pane-header { display:flex; align-items:center; gap:7px; padding:8px 12px; border-bottom:1px solid #f0f1f4; background:#fafbfc; }
.model-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.pane-model-name { font-size:12px; font-weight:600; color:#374151; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pane-status { font-size:11px; color:#1677ff; flex-shrink:0; }
.pane-body { flex:1; overflow-y:auto; padding:12px; min-height:0; }
.pane-empty { text-align:center; color:#c0c4cc; font-size:12px; padding:28px 8px; }

/* ===== 气泡 ===== */
.msg { margin-bottom:10px; display:flex; }
.msg.user { flex-direction:row-reverse; }
.msg-text { display:inline-block; max-width:94%; padding:8px 12px; border-radius:12px; font-size:12.5px; line-height:1.65; word-break:break-word; }
.msg.user .msg-text { background:#1677ff; color:#fff; border-top-right-radius:4px; white-space:pre-wrap; }
.msg.assistant .msg-text { background:#f6f7f9; color:#1f2937; border-top-left-radius:4px; }
.msg-text.streaming::after { content:'▍'; color:#1677ff; animation:mcmp-blink 1s infinite; }
@keyframes mcmp-blink { 50% { opacity:0; } }
.msg-text :deep(p) { margin:0 0 6px; } .msg-text :deep(p:last-child) { margin-bottom:0; }
.msg-text :deep(h2),.msg-text :deep(h3) { margin:6px 0 3px; font-size:13.5px; }
.msg-text :deep(ul),.msg-text :deep(ol) { margin:4px 0; padding-left:16px; }
.msg-text :deep(pre) { background:#1e293b; color:#e2e8f0; padding:8px 10px; border-radius:8px; overflow-x:auto; font-size:11.5px; }
.msg-text :deep(code) { background:#e5e7eb; padding:1px 4px; border-radius:4px; font-size:11.5px; }
.msg-text :deep(pre code) { background:transparent; padding:0; }
.msg-text :deep(table) { border-collapse:collapse; font-size:12px; }
.msg-text :deep(th),.msg-text :deep(td) { border:1px solid #e5e7eb; padding:3px 8px; }
</style>
