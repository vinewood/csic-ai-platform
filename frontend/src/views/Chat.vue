<template>
  <div class="chat-layout">
    <!-- 左侧：历史对话列表 -->
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" :icon="Plus" @click="newConv" class="new-chat-btn">新建对话</el-button>
      </div>
      <div class="conv-list">
        <div v-for="c in convs" :key="c.id" :class="['conv-item',{active:activeConv===c.id}]" @click="switchConv(c)">
          <div class="conv-title" :title="c.title">{{ c.title }}</div>
          <div class="conv-time">{{ c.time }}</div>
          <el-button link size="small" class="conv-del" @click.stop="delConv(c)"><el-icon><Delete /></el-icon></el-button>
        </div>
        <div v-if="convs.length===0" class="conv-empty">暂无历史对话</div>
      </div>
    </aside>

    <!-- 右侧：对话区 -->
    <div class="chat-main">
      <!-- 工具栏 -->
      <div class="chat-tools">
        <el-radio-group v-model="mode" size="small">
          <el-radio-button value="single">单模型</el-radio-button>
          <el-radio-button value="multi">多模型对比</el-radio-button>
        </el-radio-group>

        <template v-if="mode==='single'">
          <el-select v-model="model" size="small" style="width:150px">
            <el-option v-for="m in modelList" :key="m" :label="modelLabel(m)" :value="m" />
          </el-select>
        </template>
        <template v-else>
          <el-select v-model="multiModels" size="small" style="width:220px" multiple collapse-tags
                     :multiple-limit="6" placeholder="选择2-6个模型">
            <el-option v-for="m in modelList" :key="m" :label="modelLabel(m)" :value="m" />
          </el-select>
          <!-- 宫格布局切换：2/4/6 宫格 -->
          <div class="grid-switch">
            <button v-for="g in gridModes" :key="g.key"
                    :class="['grid-btn',{active:gridMode===g.key}]"
                    :title="g.label" @click="gridMode=g.key">
              <span class="grid-icon" :data-cols="g.cols" :data-cells="g.cells">
                <i v-for="n in g.cells" :key="n"></i>
              </span>
              {{ g.label }}
            </button>
          </div>
        </template>

        <el-select v-model="activeSkill" size="small" style="width:130px" placeholder="技能" clearable>
          <el-option v-for="s in skills" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-select v-model="kbId" size="small" style="width:130px" placeholder="知识库" clearable>
          <el-option v-for="k in kbs" :key="k.id" :label="k.name" :value="k.id" />
        </el-select>
      </div>

      <!-- 对话内容区 -->
      <div class="chat-body" ref="bodyRef">
        <!-- 空状态 -->
        <div v-if="showEmpty" class="empty-state">
          <div class="empty-logo">🎓</div>
          <h3>中船党校 AI 助手</h3>
          <p>{{ mode==='multi' ? '多模型对比模式：同一问题，多家大模型同屏作答，区块可最大化聚焦' : '输入消息开始与 AI 对话' }}</p>
          <div class="quick-prompts">
            <span v-for="q in quickPrompts" :key="q" class="prompt-chip" @click="send(q)">{{ q }}</span>
          </div>
        </div>

        <!-- 单模型：消息流 -->
        <template v-if="mode==='single'">
          <div v-for="(m,i) in msgs" :key="i" :class="['msg',m.role]">
            <div class="msg-avatar">{{ m.role==='user' ? '我' : 'AI' }}</div>
            <div class="msg-text" :class="{streaming: thinking && i===msgs.length-1 && m.role==='assistant'}"
                 v-html="render(m.content)"></div>
          </div>
        </template>

        <!-- 多模型：宫格工作台（共享组件） -->
        <ModelCompareGrid v-else ref="gridRef"
          :models="multiModels" :grid-mode="gridMode"
          :get-conv-id="() => activeConv" :extra-fn="chatExtra"
          @meta="onGridMeta" @busy="v => thinking = v" />
      </div>

      <!-- 输入框 -->
      <div class="chat-input">
        <el-upload :show-file-list="false" :before-upload="handleUpload" accept=".pdf,.docx,.txt,.md,.jpg,.png">
          <el-button circle size="small" title="上传附件"><el-icon><UploadFilled /></el-icon></el-button>
        </el-upload>
        <el-input v-model="input" type="textarea" :rows="2"
                  :placeholder="mode==='multi' ? `同一问题将同时发送给 ${multiModels.length} 个模型，Enter 发送` : '输入消息，Enter 发送'"
                  @keydown.enter.exact.prevent="send(input)" resize="none" />
        <el-button type="primary" @click="send(input)" :loading="thinking">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * AI 对话页
 * - 单模型：经典消息流
 * - 多模型对比：宫格工作台（共享组件 ModelCompareGrid）
 *   2/4/6 宫格切换，区块可最大化/还原（v3.1.0 新增）
 */
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, UploadFilled, Delete } from '@element-plus/icons-vue'
import { apiGet, apiDelete } from '../api.js'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import ModelCompareGrid from '../components/ModelCompareGrid.vue'

const route = useRoute()
const input = ref(''), mode = ref('single'), model = ref('deepseek'), multiModels = ref(['deepseek','qwen'])
const activeSkill = ref(''), kbId = ref(''), thinking = ref(false)
const msgs = ref([]), convs = ref([]), activeConv = ref('new')
const skills = ref([]), kbs = ref([])
const modelList = ['deepseek','qwen','qwen-plus','qwen-max','glm-4','kimi','minimax']
const bodyRef = ref(null)

// ---- 多模型宫格 ----
const gridMode = ref('grid4')
const gridModes = [
  { key:'grid2', label:'2宫格', cols:2, cells:2 },
  { key:'grid4', label:'4宫格', cols:2, cells:4 },
  { key:'grid6', label:'6宫格', cols:3, cells:6 },
]
const gridRef = ref(null)
const multiStarted = ref(false)          // 宫格会话是否已开始（控制空状态）

const showEmpty = computed(() =>
  mode.value === 'single' ? msgs.value.length === 0 : !multiStarted.value
)

const MODEL_LABELS = {
  deepseek:'DeepSeek', qwen:'通义千问', 'qwen-plus':'Qwen Plus', 'qwen-max':'Qwen Max',
  'glm-4':'智谱GLM', kimi:'Kimi', minimax:'MiniMax',
}
const modelLabel = m => MODEL_LABELS[m] || m

const quickPrompts = ['党建课题设计','干部培训方案','论文润色','船舶行业动态']

// 宫格附加请求字段（技能/知识库外挂）
const chatExtra = () => ({ skill_id: activeSkill.value || '', kb_id: kbId.value || '' })
// 宫格首发请求建立会话后回传 conversation_id
function onGridMeta(id) {
  if (activeConv.value === 'new') {
    activeConv.value = id
    refreshConvs()
  }
}

onMounted(async () => {
  const [sdata, kdata, cdata] = await Promise.all([
    apiGet('/api/skills'), apiGet('/api/knowledge'), apiGet('/api/chat/conversations')
  ])
  if (sdata) skills.value = sdata
  if (kdata) kbs.value = Array.isArray(kdata) ? kdata : (kdata.items||[])
  if (cdata) convs.value = cdata.map(c => ({id:c.id,title:c.title||c.name||'对话',time:c.created_at?.slice(0,10)||'刚刚'}))

  const skillId = route.query.skill
  if (skillId) activeSkill.value = skillId
})

async function refreshConvs() {
  const cdata = await apiGet('/api/chat/conversations')
  if (cdata) convs.value = cdata.map(c => ({id:c.id,title:c.title||c.name||'对话',time:c.created_at?.slice(0,10)||'刚刚'}))
}

function newConv() {
  activeConv.value = 'new'; msgs.value = []
  multiStarted.value = false
  gridRef.value?.clear()
}
function switchConv(c) {
  activeConv.value = c.id
  loadMessages(c.id)   // 历史消息在单模型流中回放；宫格区块为本次会话状态
}
async function delConv(c) {
  await apiDelete(`/api/chat/conversations/${c.id}`)
  convs.value = convs.value.filter(x => x.id !== c.id)
  if (activeConv.value === c.id) newConv()
}
async function loadMessages(convId) {
  const data = await apiGet(`/api/chat/conversations/${convId}/messages`)
  msgs.value = data ? data.map(m => ({ role: m.role, content: m.content })) : []
}

async function send(text) {
  const t = typeof text === 'string' ? text : input.value
  if (!t || !t.trim() || thinking.value) return
  if (mode.value === 'multi' && multiModels.value.length === 0) {
    ElMessage.warning('请先选择至少一个对比模型'); return
  }
  input.value = ''

  if (mode.value === 'single') {
    thinking.value = true
    msgs.value.push({ role: 'user', content: t.trim() })
    msgs.value.push({ role: 'assistant', content: '' })
    await nextTick(); scrollBottom()
    await streamChat(t.trim(), msgs.value[msgs.value.length-1], model.value)
    thinking.value = false
    await nextTick(); scrollBottom()
  } else {
    // 宫格模式：交给共享组件并行广播（busy 事件驱动 thinking）
    multiStarted.value = true
    await gridRef.value?.broadcast(t.trim())
  }
}

async function streamChat(query, target, mdl) {
  const token = localStorage.getItem('csic_token')
  const API_BASE = window.location.port === '5173' ? 'http://localhost:8000' : ''
  try {
    const resp = await fetch(`${API_BASE}/api/chat/dify-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        query, model: mdl,
        conversation_id: activeConv.value === 'new' ? '' : activeConv.value,
        skill_id: activeSkill.value || '',
        kb_id: kbId.value || ''
      })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })
      for (const line of text.split('\n')) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const json = JSON.parse(data)
            if (json.conversation_id && activeConv.value === 'new') {
              activeConv.value = json.conversation_id
              refreshConvs()
            }
            if (json.content) {
              fullContent += json.content
              target.content = fullContent
            }
          } catch (e) { /* 半包 JSON 忽略，下一片段补齐 */ }
        }
      }
    }
  } catch (e) {
    target.content = `[错误] ${e.message}`
  }
}

function render(text) {
  if (!text) return ''
  const cleaned = text.replace(/\n{3,}/g, '\n\n')
  try { return marked.parse(cleaned) } catch { return cleaned }
}
function scrollBottom() {
  nextTick(() => { if(bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight })
}

async function handleUpload(file) {
  const formData = new FormData(); formData.append('file', file)
  msgs.value.push({ role: 'user', content: `📎 ${file.name}` })
  thinking.value = true
  try {
    const token = localStorage.getItem('csic_token')
    const API_BASE = window.location.port === '5173' ? 'http://localhost:8000' : ''
    const resp = await fetch(`${API_BASE}/api/files/upload`, {
      method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: formData
    })
    const data = await resp.json()
    msgs.value.push({ role: 'assistant', content: `文件已上传，内容预览：\n\n${(data.result||data.text||'').slice(0, 2000)}` })
  } catch (e) {
    msgs.value.push({ role: 'assistant', content: `[上传失败: ${e.message}]` })
  } finally { thinking.value = false }
  return false
}
</script>

<style scoped>
/* ===== 布局骨架 ===== */
.chat-layout { display:flex; height:calc(100vh - 160px); background:#f7f8fa; }
.chat-sidebar { width:216px; min-width:216px; background:#fff; border-right:1px solid #ebedf0; display:flex; flex-direction:column; }
.sidebar-header { padding:12px; }
.new-chat-btn { width:100%; }
.conv-list { flex:1; overflow-y:auto; padding:0 8px 12px; }
.conv-item { padding:9px 10px; border-radius:8px; cursor:pointer; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center; transition:background .15s; }
.conv-item:hover { background:#f4f6fb; }
.conv-item.active { background:#eaf1ff; }
.conv-item.active .conv-title { color:#1677ff; font-weight:600; }
.conv-title { font-size:13px; color:#1f2937; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.conv-time { font-size:10px; color:#9ca3af; margin-left:8px; }
.conv-del { opacity:0; }
.conv-item:hover .conv-del { opacity:1; }
.conv-empty { text-align:center; color:#bbb; padding:24px 0; font-size:12px; }

.chat-main { flex:1; display:flex; flex-direction:column; min-width:0; }
.chat-tools { padding:8px 14px; background:#fff; border-bottom:1px solid #ebedf0; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.chat-body { flex:1; overflow-y:auto; padding:16px 20px; min-height:0; display:flex; flex-direction:column; }
.chat-body > * { flex:0 0 auto; }
.chat-body > .mcmp-wrap { flex:1 1 auto; min-height:0; }

/* ===== 空状态 ===== */
.empty-state { text-align:center; padding:56px 20px; color:#9ca3af; margin:auto; }
.empty-logo { font-size:44px; margin-bottom:8px; }
.empty-state h3 { margin:0 0 6px; color:#374151; font-size:18px; }
.empty-state p { margin:0 0 18px; font-size:13px; }
.quick-prompts { display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }
.prompt-chip { padding:6px 14px; background:#fff; border:1px solid #e5e7eb; border-radius:999px; font-size:12px; color:#4b5563; cursor:pointer; transition:all .15s; }
.prompt-chip:hover { border-color:#1677ff; color:#1677ff; box-shadow:0 2px 8px rgba(22,119,255,.12); }

/* ===== 宫格切换按钮 ===== */
.grid-switch { display:flex; gap:4px; background:#f3f4f6; padding:3px; border-radius:8px; }
.grid-btn { display:flex; align-items:center; gap:5px; border:none; background:transparent; padding:4px 10px; border-radius:6px; font-size:12px; color:#6b7280; cursor:pointer; transition:all .15s; }
.grid-btn:hover { color:#1677ff; }
.grid-btn.active { background:#fff; color:#1677ff; font-weight:600; box-shadow:0 1px 3px rgba(0,0,0,.08); }
.grid-icon { display:grid; gap:1.5px; width:16px; height:12px; }
.grid-icon[data-cols="2"] { grid-template-columns:repeat(2,1fr); }
.grid-icon[data-cols="3"] { grid-template-columns:repeat(3,1fr); }
.grid-icon i { background:currentColor; border-radius:1px; opacity:.75; }

/* ===== 消息气泡 ===== */
.msg { margin-bottom:12px; display:flex; gap:8px; align-items:flex-start; }
.msg-avatar { width:26px; height:26px; min-width:26px; border-radius:50%; background:#eef2ff; color:#1677ff; font-size:11px; display:flex; align-items:center; justify-content:center; }
.msg.user { flex-direction:row-reverse; }
.msg.user .msg-avatar { background:#1677ff; color:#fff; }
.msg-text { display:inline-block; max-width:82%; padding:9px 13px; border-radius:12px; font-size:13px; line-height:1.65; word-break:break-word; }
.msg.user .msg-text { background:#1677ff; color:#fff; border-top-right-radius:4px; white-space:pre-wrap; }
.msg.assistant .msg-text { background:#fff; color:#1f2937; border:1px solid #eef0f3; border-top-left-radius:4px; box-shadow:0 1px 2px rgba(16,24,40,.04); }
.msg-text.streaming::after { content:'▍'; color:#1677ff; animation:blink 1s infinite; }
@keyframes blink { 50% { opacity:0; } }
.msg-text :deep(p) { margin:0 0 6px; } .msg-text :deep(p:last-child) { margin-bottom:0; }
.msg-text :deep(pre) { background:#1e293b; color:#e2e8f0; padding:8px 12px; border-radius:8px; overflow-x:auto; font-size:12px; }
.msg-text :deep(code) { background:#eef0f3; padding:1px 4px; border-radius:4px; font-size:12px; }
.msg-text :deep(pre code) { background:transparent; padding:0; }
.msg.user .msg-text :deep(code) { background:rgba(255,255,255,.2); }

/* ===== 输入区 ===== */
.chat-input { padding:10px 14px; background:#fff; border-top:1px solid #ebedf0; display:flex; gap:8px; align-items:center; }
.chat-input :deep(.el-textarea__inner) { border-radius:10px; font-size:13px; padding:8px 12px; box-shadow:0 0 0 1px #e5e7eb inset; }
.chat-input :deep(.el-textarea__inner:focus) { box-shadow:0 0 0 1.5px #1677ff inset; }
</style>
