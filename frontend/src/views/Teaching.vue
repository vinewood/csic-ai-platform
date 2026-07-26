<template>
  <div class="teach-layout">
    <!-- 左栏：教学功能 + 历史 -->
    <div class="teach-panel">
      <el-button type="primary" :icon="Plus" size="small" class="new-btn" @click="newConv">新建对话</el-button>

      <div class="panel-title" style="margin-top:12px">教学功能</div>
      <div class="func-list">
        <div v-for="f in teachFuncs" :key="f.id" class="func-btn" :class="{active:f.id===funcId}" @click="useFunc(f)">
          <el-icon :size="15"><component :is="f.icon" /></el-icon>{{ f.label }}
        </div>
      </div>

      <div class="panel-divider"></div>
      <div class="panel-title">历史对话</div>
      <div class="hist-list">
        <div v-for="c in convs" :key="c.id" class="hist-item" :class="{active:c.id===convId}" :title="c.title||'对话'" @click="loadConv(c)">
          <span class="hist-title">{{ c.title || '对话' }}</span>
          <el-dropdown trigger="click" @command="(cmd)=>histAction(cmd,c)">
            <el-button link size="small" class="hist-btn" @click.stop><el-icon><MoreFilled /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename"><el-icon><EditPen /></el-icon> 重命名</el-dropdown-item>
                <el-dropdown-item command="pin"><el-icon><Top /></el-icon> 置顶</el-dropdown-item>
                <el-dropdown-item command="docx"><el-icon><Download /></el-icon> 保存到本地</el-dropdown-item>
                <el-dropdown-item command="skill"><el-icon><MagicStick /></el-icon> 整理成技能</el-dropdown-item>
                <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div v-if="convs.length===0" class="csic-empty csic-empty--sm"><span class="empty-icon">📝</span><span class="empty-title">暂无历史</span></div>
      </div>
    </div>

    <!-- 中栏：对话主区 -->
    <div class="chat-main">
      <!-- 顶栏：模型 chips 选择（选1个=单聊，选2-6个=自动宫格对比） -->
      <div class="chat-tools">
        <div class="model-chips">
          <button v-for="m in models" :key="m.value"
                  :class="['model-chip', { active: picked.includes(m.value) }]"
                  :style="picked.includes(m.value) ? { borderColor: modelColor(m.value), color: modelColor(m.value) } : {}"
                  @click="toggleModel(m.value)">
            <span class="chip-dot" :style="{ background: modelColor(m.value) }"></span>{{ m.label }}
          </button>
          <span class="chip-hint">{{ picked.length > 1 ? `已选 ${picked.length} 个模型 · 自动 ${picked.length} 宫格` : '单模型对话 · 再点选模型即自动宫格对比' }}</span>
        </div>
        <el-select v-model="kbId" size="small" style="width:130px;margin-left:4px" clearable placeholder="知识库">
          <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id">
            <span>{{ kb.name }}</span><span style="color:#bbb;font-size:10px;margin-left:6px">{{ kb.count }}篇</span>
          </el-option>
        </el-select>
        <el-button size="small" :icon="Plus" @click="newConv" circle />
        <el-button size="small" @click="saveResult" :disabled="mode==='single' ? msgs.length===0 : !multiStarted" style="margin-left:auto">保存</el-button>
      </div>

      <!-- 对话区 -->
      <div class="chat-body" ref="bodyRef">
        <div v-if="showEmpty" class="empty">
          <p>选择左侧教学功能或直接输入教学需求</p>
          <p v-if="mode==='multi'" style="font-size:12px;color:#b6bbc4">已选 {{ picked.length }} 个模型：同一问题同屏对比作答，区块可最大化聚焦</p>
          <div class="quick-btns">
            <el-button v-for="q in quickBtns" :key="q.id" size="small" round @click="input=q.prompt;doSend()">{{ q.label }}</el-button>
          </div>
        </div>

        <!-- 单模型：消息流 -->
        <template v-if="mode==='single'">
          <div v-for="(m,i) in msgs" :key="i" :class="['msg',m.role]">
            <div class="msg-text" v-html="render(m.content)"></div>
          </div>
          <div v-if="thinking" class="msg assistant"><div class="msg-text thinking-dots">思考中…</div></div>
        </template>

        <!-- 多模型：宫格工作台（共享组件，布局随模型数自动） -->
        <ModelCompareGrid v-else ref="gridRef"
          :models="multiModels"
          :get-conv-id="() => convId" :extra-fn="teachExtra"
          @meta="onGridMeta" @busy="v => thinking = v" />
      </div>

      <!-- 输入区 -->
      <div class="chat-input">
        <div v-if="skillId" class="skill-badge">
          <el-tag type="warning" size="small" closable @close="skillId=''">🔧 {{ getSkillName(skillId) }}</el-tag>
        </div>
        <div class="input-row">
          <el-upload :show-file-list="false" :before-upload="handleUpload" accept=".pdf,.docx,.txt,.md">
            <el-button circle size="small"><el-icon><UploadFilled /></el-icon></el-button>
          </el-upload>
          <el-input v-model="input" type="textarea" :rows="3"
            :placeholder="mode==='multi' ? `同一问题将同时发送给 ${multiModels.length} 个模型，Enter 发送` : '输入教学需求，Enter 发送'"
            @keydown.enter.exact.prevent="doSend" resize="none" />
          <el-button type="primary" @click="doSend" :loading="thinking" size="small">发送</el-button>
        </div>
      </div>
    </div>

    <!-- 右栏：技能中心 -->
    <div class="skill-panel">
      <div class="panel-title">技能中心</div>
      <div class="skill-list">
        <div v-for="s in skills" :key="s.id" class="skill-btn" :class="{active:s.id===skillId}" @click="skillId=s.id;ElMessage.success('已挂载技能: '+s.name)">
          <el-icon :size="14"><component :is="iconMap[s.icon] || MagicStick" /></el-icon>
          <span>{{ s.name }}</span>
        </div>
        <div v-if="skills.length===0" class="csic-empty csic-empty--sm"><span class="empty-icon">✨</span><span class="empty-title">暂无技能</span></div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 教学工作台
 * - 单模型：消息流 + 教学功能快捷入口
 * - 多模型对比：宫格工作台（共享组件 ModelCompareGrid，v3.1.0）
 * 修复：apiPost 未导入导致"整理成技能"必崩；多模型会话 id 未回传导致每次新建多个会话
 */
import { ref, computed, onMounted, nextTick } from 'vue'
import { Plus, UploadFilled, EditPen, Document, DataBoard, Notebook, MagicStick, MoreFilled, Top, Download, Delete } from '@element-plus/icons-vue'
import * as Icons from '@element-plus/icons-vue'
import { apiGet, apiDelete, apiPost } from '../api.js'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import ModelCompareGrid from '../components/ModelCompareGrid.vue'
import { modelColor } from '../utils/models.js'

const iconMap = { ...Icons }

const teachFuncs = [
  { id: 'topics', label: '课题选题', icon: EditPen, prompt: '请帮我为【填写培训方向】设计5个教学课题' },
  { id: 'outline', label: '课程大纲', icon: Document, prompt: '请为课题【填写课题名称】生成详细教学大纲' },
  { id: 'inspire', label: '灵感激发', icon: DataBoard, prompt: '请为课题【填写课题名称】生成4条教学创意' },
  { id: 'lecture', label: '讲稿生成', icon: Notebook, prompt: '请为课题【填写课题名称】生成逐页讲稿' },
  { id: 'quiz', label: '试题生成', icon: MagicStick, prompt: '请为课题【填写课题名称】出一套考试题' },
]

const quickBtns = [
  { id: 'q1', label: '生成3个党建培训课题', prompt: '请为基层党建培训设计3个教学课题' },
  { id: 'q2', label: '二十大精神培训大纲', prompt: '请为党的二十大精神专题培训生成教学大纲' },
  { id: 'q3', label: '干部能力提升课程方案', prompt: '请为中青年干部能力提升设计课程方案' },
]

const input = ref('')
const thinking = ref(false), msgs = ref([]), skillId = ref(''), funcId = ref(''), kbId = ref(''), kbList = ref([])
const skills = ref([]), convs = ref([]), convId = ref('new')
const models = [
  { label: 'DeepSeek V4 Pro', value: 'deepseek' },
  { label: 'Qwen3.7 Plus', value: 'qwen-plus' },
  { label: 'Qwen3.7 Max', value: 'qwen-max' },
  { label: 'GLM-5.2', value: 'glm-4' },
  { label: 'Kimi K2.7 Code', value: 'kimi' },
  { label: 'MiniMax M2.5', value: 'minimax' },
]
const bodyRef = ref(null)

// ---- 模型选择（chips 单一数据源）：选 1 个=单聊，选 2-6 个=自动宫格 ----
const picked = ref(['deepseek'])
const mode = computed({
  get: () => picked.value.length > 1 ? 'multi' : 'single',
  set: v => { if (v === 'single') picked.value = [picked.value[0]] },
})
const model = computed({
  get: () => picked.value[0],
  set: v => { picked.value = [v] },
})
const multiModels = computed({
  get: () => picked.value,
  set: v => { if (Array.isArray(v) && v.length) picked.value = [...new Set(v)].slice(0, 6) },
})
function toggleModel(m) {
  if (picked.value.includes(m)) {
    if (picked.value.length > 1) picked.value = picked.value.filter(x => x !== m)  // 至少保留 1 个
  } else {
    if (picked.value.length >= 6) { ElMessage.warning('最多同时对比 6 个模型'); return }
    picked.value = [...picked.value, m]
  }
}

const gridRef = ref(null)
const multiStarted = ref(false)

const showEmpty = computed(() =>
  mode.value === 'single' ? msgs.value.length === 0 : !multiStarted.value
)

const teachExtra = () => ({ skill_id: skillId.value || '' })
function onGridMeta(id) {
  if (convId.value === 'new') { convId.value = id; refreshConvs() }
}

onMounted(async () => {
  const [s, c, k] = await Promise.all([apiGet('/api/skills'), apiGet('/api/chat/conversations'), apiGet('/api/dify/datasets/list')])
  if (s) skills.value = s
  if (c) convs.value = c.map(x => ({ id:x.id, title:x.title||'对话', time:x.created_at?.slice(0,10)||'' }))
  if (k) kbList.value = k
})

function newConv() {
  convId.value = 'new'; msgs.value = []
  multiStarted.value = false
  gridRef.value?.clear()
}

function useFunc(f) {
  funcId.value = f.id
  input.value = f.prompt
  nextTick(() => {
    const ta = document.querySelector('.chat-input textarea')
    if (ta) {
      ta.focus()
      // 选中【...】内的占位文字
      const match = f.prompt.match(/【(.+?)】/)
      if (match) {
        const start = f.prompt.indexOf(match[0])
        ta.setSelectionRange(start, start + match[0].length)
      }
    }
  })
}
/**
 * 历史消息按轮次分组：
 * 连续的 user 消息开启新一轮（多模型旧数据的 N 条重复 user 只取第一条），
 * 随后的 assistant 消息按 model 归入 answers，供宫格重建
 */
function groupRounds(list) {
  const rounds = []
  let cur = null
  for (const m of list) {
    if (m.role === 'user') {
      if (!cur || cur.answers.length > 0) { cur = { question: m.content, answers: [] }; rounds.push(cur) }
    } else {
      if (!cur) { cur = { question: '', answers: [] }; rounds.push(cur) }
      cur.answers.push({ model: m.model || '', content: m.content })
    }
  }
  return rounds
}

async function loadConv(c) {
  convId.value = c.id
  const data = await apiGet(`/api/chat/conversations/${c.id}/messages`)
  const list = data ? data.map(m => ({ role: m.role, content: m.content, model: m.model || '' })) : []
  msgs.value = list
  const rounds = groupRounds(list)
  const isMultiHistory = rounds.some(r => r.answers.filter(a => a.model).length > 1)

  if (isMultiHistory || mode.value === 'multi') {
    // 多模型历史（或当前处于多模型视图）：重建宫格对比界面
    if (isMultiHistory) mode.value = 'multi'   // 自动切到多模型视图
    await nextTick()
    const order = gridRef.value?.loadRounds(rounds) || []
    if (order.length) {
      multiModels.value = order
      multiStarted.value = true
    } else if (list.length) {
      // 宫格功能上线前的旧历史没有模型标识，回退单模型视图
      mode.value = 'single'
      ElMessage.info('该历史为多模型宫格上线前的记录，已按单模型视图展示')
    }
  }
}
async function refreshConvs() {
  const c = await apiGet('/api/chat/conversations')
  if (c) convs.value = c.map(x => ({ id:x.id, title:x.title||'对话', time:x.created_at?.slice(0,10)||'' }))
}

async function saveResult() {
  if (convId.value === 'new') { ElMessage.warning('请先发送消息创建对话'); return }
  ElMessage.info('正在生成 docx...')
  const token = localStorage.getItem('csic_token')
  const API_BASE = location.port === '5173' ? 'http://localhost:8000' : ''
  try {
    const r = await fetch(`${API_BASE}/api/export/docx`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ conversation_id: convId.value })
    })
    if (r.ok) {
      const blob = await r.blob(); const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = `教学对话.docx`; a.click()
      ElMessage.success('已下载 docx')
    } else { ElMessage.error('生成失败') }
  } catch (e) { ElMessage.error(e.message) }
}

async function doSend() {
  const t = input.value.trim()
  if (!t || thinking.value) return
  if (mode.value === 'multi' && multiModels.value.length === 0) {
    ElMessage.warning('请先选择至少一个对比模型'); return
  }
  input.value = ''; funcId.value = ''

  if (mode.value === 'single') {
    thinking.value = true
    msgs.value.push({ role: 'user', content: t })
    await nextTick(); scrollBottom()
    msgs.value.push({ role: 'assistant', content: '' })
    const last = msgs.value[msgs.value.length - 1]
    const token = localStorage.getItem('csic_token')
    const API_BASE = location.port === '5173' ? 'http://localhost:8000' : ''
    try {
      const resp = await fetch(`${API_BASE}/api/chat/dify-chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: t, model: model.value, skill_id: skillId.value || '', conversation_id: convId.value })
      })
      const reader = resp.body.getReader(); const dec = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        for (const line of dec.decode(value,{stream:true}).split('\n')) {
          if (line.startsWith('data: ')) {
            const d = line.slice(6); if (d === '[DONE]') continue
            try { const j = JSON.parse(d); if (j.content) last.content += j.content
              if (j.conversation_id && convId.value==='new') { convId.value = j.conversation_id; refreshConvs() }
            } catch {}
          }
        }
      }
    } catch (e) { last.content = `[错误] ${e.message}` }
    thinking.value = false; await nextTick(); scrollBottom()
  } else {
    // 宫格模式：共享组件并行广播（busy 事件驱动 thinking）
    multiStarted.value = true
    await gridRef.value?.broadcast(t)
  }
}

async function histAction(cmd, c) {
  if (cmd === 'rename') {
    try {
      const { value } = await import('element-plus').then(m => m.ElMessageBox.prompt('请输入新名称', '重命名', { inputValue: c.title }))
      if (value && value.trim()) {
        const token = localStorage.getItem('csic_token')
        const API_BASE = location.port === '5173' ? 'http://localhost:8000' : ''
        await fetch(`${API_BASE}/api/chat/conversations/${c.id}/rename`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ title: value.trim() })
        })
        c.title = value.trim()
        ElMessage.success('已重命名')
      }
    } catch {}
  } else if (cmd === 'delete') {
    await apiDelete(`/api/chat/conversations/${c.id}`)
    convs.value = convs.value.filter(x => x.id !== c.id)
    if (convId.value === c.id) { convId.value = 'new'; msgs.value = [] }
    ElMessage.success('已删除')
  } else if (cmd === 'pin') {
    convs.value = [c, ...convs.value.filter(x => x.id !== c.id)]
    ElMessage.success('已置顶')
  } else if (cmd === 'docx') {
    ElMessage.info('正在生成 docx...')
    const token = localStorage.getItem('csic_token')
    const API_BASE = location.port === '5173' ? 'http://localhost:8000' : ''
    try {
      const r = await fetch(`${API_BASE}/api/export/docx`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ conversation_id: c.id })
      })
      if (r.ok) {
        const blob = await r.blob(); const url = URL.createObjectURL(blob)
        const a = document.createElement('a'); a.href = url; a.download = `${c.title||'对话'}.docx`; a.click()
        ElMessage.success('下载完成')
      } else { ElMessage.error('生成失败') }
    } catch (e) { ElMessage.error(e.message) }
  } else if (cmd === 'skill') {
    const data = await apiGet(`/api/chat/conversations/${c.id}/messages`)
    const content = data ? data.map(m=>`### ${m.role}\n${m.content}`).join('\n\n') : c.title
    await apiPost('/api/skills', {
      name: c.title || '新技能', description: '从对话提炼', category: '教学', icon: 'MagicStick', color: '#1677ff',
      prompt: `你根据以下对话内容扮演AI助手角色：\n\n${content.slice(0,3000)}`
    })
    ElMessage.success('已整理成技能')
  }
}

function render(t) {
  if (!t) return ''
  try { return marked.parse(t.replace(/\n{3,}/g, '\n\n')) } catch { return t }
}
function scrollBottom() { nextTick(() => { if(bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight }) }
function getSkillName(id) { const s = skills.value.find(x => String(x.id) === String(id)); return s ? s.name : '技能' }

async function handleUpload(file) {
  const formData = new FormData(); formData.append('file', file)
  msgs.value.push({ role: 'user', content: `📎 ${file.name}` })
  thinking.value = true
  try {
    const token = localStorage.getItem('csic_token')
    const API_BASE = location.port === '5173' ? 'http://localhost:8000' : ''
    const r = await fetch(`${API_BASE}/api/files/upload`, {
      method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: formData
    })
    const d = await r.json()
    msgs.value.push({ role: 'assistant', content: `已上传: ${(d.result||d.text||'').slice(0,1500)}` })
  } catch (e) { msgs.value.push({ role: 'assistant', content: `[上传失败]` }) }
  finally { thinking.value = false }
  return false
}
</script>

<style scoped>
.teach-layout { display:flex; height:calc(100vh - 160px); background:#f7f8fa; margin:0 8px; }
.teach-panel { width:170px; min-width:170px; background:#fff; border-right:1px solid #ebedf0; padding:10px 8px; display:flex; flex-direction:column; }
.new-btn { width:100%; margin-bottom:4px; }
.panel-title { font-size:10px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:1px; padding:0 4px 6px; }
.func-list { display:flex; flex-direction:column; gap:3px; margin-bottom:8px; }
.panel-divider { height:1px; background:#ebedf0; margin:8px 0; }
.hist-list { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:2px; }
.hist-item { padding:6px 8px; border-radius:6px; cursor:pointer; font-size:12px; display:flex; justify-content:space-between; transition:background .15s; }
.hist-item:hover { background:#f4f6fb; }
.hist-item.active { background:#eaf1ff; }
.hist-title { color:#374151; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.func-btn { display:flex; align-items:center; gap:6px; padding:7px 8px; border-radius:6px; cursor:pointer; font-size:12px; color:#374151; transition:background .15s; }
.func-btn:hover { background:#f4f6fb; }
.func-btn.active { background:#eaf1ff; color:#1677ff; font-weight:600; }

.chat-main { flex:1; display:flex; flex-direction:column; min-width:0; }
.chat-tools { padding:6px 12px; background:#fff; border-bottom:1px solid #ebedf0; display:flex; gap:6px; align-items:center; flex-wrap:wrap; }
.chat-body { flex:1; overflow-y:auto; padding:14px 18px; min-height:0; display:flex; flex-direction:column; }
.chat-body > * { flex:0 0 auto; }
.chat-body > .mcmp-wrap { flex:1 1 auto; min-height:0; }
.empty { text-align:center; padding:50px 20px; color:#9ca3af; margin:auto; }
.quick-btns { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; justify-content:center; }
.msg { margin-bottom:12px; display:flex; }
.msg.user { flex-direction:row-reverse; }
.msg-text { display:inline-block; max-width:80%; padding:9px 13px; border-radius:12px; font-size:13px; line-height:1.7; word-break:break-word; }
.msg.user .msg-text { background:#1677ff; color:#fff; border-top-right-radius:4px; }
.msg.assistant .msg-text { background:#fff; color:#1f2937; border:1px solid #eef0f3; border-top-left-radius:4px; box-shadow:0 1px 2px rgba(16,24,40,.04); }
.thinking-dots { color:#9ca3af; }
.msg-text :deep(h2),.msg-text :deep(h3) { margin:6px 0 3px; font-size:14px; }
.msg-text :deep(p) { margin:0 0 6px; } .msg-text :deep(p:last-child) { margin-bottom:0; }
.msg-text :deep(ul),.msg-text :deep(ol) { margin:4px 0; padding-left:16px; }
.msg-text :deep(pre) { background:#1e293b;color:#e2e8f0;padding:6px 10px;border-radius:8px;overflow-x:auto;font-size:11.5px; }
.msg-text :deep(code) { background:#eef0f3;padding:1px 4px;border-radius:4px;font-size:11.5px; }
.msg-text :deep(pre code) { background:transparent; padding:0; }

/* ===== 模型 chips 选择器（选 2-6 个自动成宫格，与 Chat 页一致） ===== */
.model-chips { display:flex; gap:6px; align-items:center; flex-wrap:wrap; }
.model-chip { display:flex; align-items:center; gap:5px; border:1px solid #e5e7eb; background:#fff; padding:4px 10px; border-radius:16px; font-size:12px; color:#6b7280; cursor:pointer; transition:all .15s; }
.model-chip:hover { border-color:#c7d2fe; color:#374151; }
.model-chip.active { background:#f5f7ff; font-weight:600; }
.chip-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
.chip-hint { font-size:11px; color:#9ca3af; margin-left:2px; }

.chat-input { padding:8px 12px; background:#fff; border-top:1px solid #ebedf0; }
.skill-badge { padding:4px 0; }
.input-row { display:flex; gap:6px; align-items:center; }
.chat-input :deep(.el-textarea__inner) { border-radius:10px; font-size:13px; padding:8px 10px; }

.skill-panel { width:160px; min-width:160px; background:#fff; border-left:1px solid #ebedf0; padding:10px 8px; overflow:hidden; display:flex; flex-direction:column; }
.skill-list { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:3px; }
.skill-btn { display:flex; align-items:center; gap:6px; padding:6px 8px; border-radius:6px; cursor:pointer; font-size:12px; color:#374151; transition:background .15s; }
.skill-btn:hover { background:#f4f6fb; }
.skill-btn.active { background:#eaf1ff; color:#1677ff; font-weight:600; }
.skill-btn span { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

@media (max-width:768px) { .teach-panel,.skill-panel { display:none; } .teach-layout { margin:0; } }
</style>
