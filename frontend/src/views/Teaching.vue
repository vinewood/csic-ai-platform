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
        <div v-for="c in convs" :key="c.id" class="hist-item" :class="{active:c.id===convId}" @click="loadConv(c)">
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
        <div v-if="convs.length===0" style="color:#bbb;font-size:11px;text-align:center;padding:10px">暂无历史</div>
      </div>
    </div>

    <!-- 中栏：对话主区 -->
    <div class="chat-main">
      <!-- 顶栏 -->
      <div class="chat-tools">
        <el-radio-group v-model="mode" size="small">
          <el-radio-button value="single">单模型</el-radio-button>
          <el-radio-button value="multi">多模型</el-radio-button>
        </el-radio-group>
        <template v-if="mode==='single'">
          <el-select v-model="model" size="small" style="width:110px">
            <el-option v-for="m in models" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </template>
        <template v-else>
          <el-select v-model="multiModels" size="small" style="width:200px" multiple collapse-tags>
            <el-option v-for="m in models" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </template>
        <el-select v-model="kbId" size="small" style="width:140px;margin-left:4px" clearable placeholder="知识库">
          <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id">
            <span>{{ kb.name }}</span><span style="color:#bbb;font-size:10px;margin-left:6px">{{ kb.count }}篇</span>
          </el-option>
        </el-select>
        <el-button size="small" :icon="Plus" @click="newConv" circle />
        <el-button size="small" @click="saveResult" :disabled="msgs.length===0" style="margin-left:auto">保存</el-button>
      </div>

      <!-- 对话区 -->
      <div class="chat-body" ref="bodyRef">
        <div v-if="msgs.length===0" class="empty">
          <p>选择左侧教学功能或直接输入教学需求</p>
          <div class="quick-btns">
            <el-button v-for="q in quickBtns" :key="q.id" size="small" round @click="input=q.prompt;doSend()">{{ q.label }}</el-button>
          </div>
        </div>
        <div v-for="(m,i) in msgs" :key="i">
          <template v-if="m.results">
            <div class="msg user"><div class="msg-text">{{ m.content }}</div></div>
            <div class="multi-grid">
              <div v-for="r in m.results" :key="r.model" class="multi-cell">
                <div class="multi-label">{{ r.model }}</div>
                <div class="msg-text" v-html="render(r.content)"></div>
              </div>
            </div>
          </template>
          <div v-else :class="['msg',m.role]">
            <div class="msg-text" v-html="render(m.content)"></div>
          </div>
        </div>
        <div v-if="thinking" class="msg assistant"><div class="msg-text">...</div></div>
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
          <el-input v-model="input" type="textarea" :rows="3" placeholder="输入教学需求，Enter 发送"
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
        <div v-if="skills.length===0" style="color:#bbb;font-size:11px;text-align:center;padding:10px">暂无技能</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Plus, UploadFilled, EditPen, Document, DataBoard, Notebook, MagicStick, MoreFilled, Top, Download, Delete } from '@element-plus/icons-vue'
import * as Icons from '@element-plus/icons-vue'
import { apiGet, apiDelete } from '../api.js'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'

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

const input = ref(''), mode = ref('single'), model = ref('deepseek'), multiModels = ref(['deepseek','qwen-plus'])
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

onMounted(async () => {
  const [s, c, k] = await Promise.all([apiGet('/api/skills'), apiGet('/api/chat/conversations'), apiGet('/api/dify/datasets/list')])
  if (s) skills.value = s
  if (c) convs.value = c.map(x => ({ id:x.id, title:x.title||'对话', time:x.created_at?.slice(0,10)||'' }))
  if (k) kbList.value = k
})

function newConv() { convId.value = 'new'; msgs.value = [] }

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
async function loadConv(c) {
  convId.value = c.id
  const data = await apiGet(`/api/chat/conversations/${c.id}/messages`)
  msgs.value = data ? data.map(m => ({ role: m.role, content: m.content })) : []
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
  input.value = ''; thinking.value = true; funcId.value = ''
  msgs.value.push({ role: 'user', content: t })
  await nextTick(); scrollBottom()

  const token = localStorage.getItem('csic_token')
  const API_BASE = location.port === '5173' ? 'http://localhost:8000' : ''

  if (mode.value === 'single') {
    msgs.value.push({ role: 'assistant', content: '' })
    const last = msgs.value[msgs.value.length - 1]
    try {
      const resp = await fetch(`${API_BASE}/api/chat/dify-chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: t, model: model.value, skill_id: skillId.value || '' })
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
  } else {
    // 多模型对比
    const results = multiModels.value.map(m => ({ model: m, content: '' }))
    msgs.value.push({ role: 'assistant', results })
    const last = msgs.value[msgs.value.length - 1]
    await Promise.all(multiModels.value.map(async (m, i) => {
      try {
        const resp = await fetch(`${API_BASE}/api/chat/dify-chat`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ query: t, model: m, skill_id: skillId.value || '' })
        })
        const reader = resp.body.getReader(); const dec = new TextDecoder()
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          for (const line of dec.decode(value,{stream:true}).split('\n')) {
            if (line.startsWith('data: ')) {
              const d = line.slice(6); if (d === '[DONE]') continue
              try { const j = JSON.parse(d); if (j.content) last.results[i].content += j.content } catch {}
            }
          }
        }
      } catch (e) { last.results[i].content = `[错误] ${e.message}` }
    }))
  }
  thinking.value = false; await nextTick(); scrollBottom()
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
.teach-layout { display:flex; height:calc(100vh - 160px); background:#fff; margin:0 8px; }
.teach-panel { width:170px; min-width:170px; background:#f8f9fb; border-right:1px solid #e5e7eb; padding:10px 8px; display:flex; flex-direction:column; }
.new-btn { width:100%; margin-bottom:4px; }
.panel-title { font-size:10px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:1px; padding:0 4px 6px; }
.func-list { display:flex; flex-direction:column; gap:3px; margin-bottom:8px; }
.panel-divider { height:1px; background:#e5e7eb; margin:8px 0; }
.hist-list { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:2px; }
.hist-item { padding:5px 8px; border-radius:5px; cursor:pointer; font-size:12px; display:flex; justify-content:space-between; }
.hist-item:hover,.hist-item.active { background:#f0f5ff; }
.hist-title { color:#374151; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.hist-time { color:#bbb; font-size:10px; margin-left:4px; flex-shrink:0; }
.func-btn { display:flex; align-items:center; gap:6px; padding:7px 8px; border-radius:6px; cursor:pointer; font-size:12px; color:#374151; }
.func-btn:hover { background:#e8ecf1; }
.func-btn.active { background:#1677ff12; color:#1677ff; font-weight:600; }

.chat-main { flex:1; display:flex; flex-direction:column; min-width:0; }
.chat-tools { padding:5px 10px; border-bottom:1px solid #e5e7eb; display:flex; gap:6px; align-items:center; }
.chat-body { flex:1; overflow-y:auto; padding:10px 20px; }
.empty { text-align:center; padding:50px 20px; color:#9ca3af; }
.quick-btns { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; justify-content:center; }
.msg { margin-bottom:10px; }
.msg.user { text-align:right; }
.msg-text { display:inline-block; max-width:80%; padding:7px 12px; border-radius:10px; font-size:13px; line-height:1.7; word-break:break-word; }
.msg.user .msg-text { background:#1677ff; color:#fff; }
.msg.assistant .msg-text { background:#f3f4f6; color:#1f2937; }
.msg-text :deep(h2),.msg-text :deep(h3) { margin:4px 0 2px; font-size:14px; }
.msg-text :deep(p) { margin:3px 0; }
.msg-text :deep(ul),.msg-text :deep(ol) { margin:3px 0; padding-left:16px; }
.msg-text :deep(pre) { background:#1e293b;color:#e2e8f0;padding:5px 8px;border-radius:5px;overflow-x:auto;font-size:11px; }
.msg-text :deep(code) { background:#e5e7eb;padding:1px 3px;border-radius:3px;font-size:11px; }

.chat-input { padding:8px 12px; border-top:1px solid #e5e7eb; }
.skill-badge { padding:4px 0; }
.input-row { display:flex; gap:6px; align-items:center; }
.chat-input :deep(.el-textarea__inner) { border-radius:8px; font-size:13px; padding:6px 8px; }

.skill-panel { width:160px; min-width:160px; background:#f8f9fb; border-left:1px solid #e5e7eb; padding:10px 8px; overflow:hidden; display:flex; flex-direction:column; }
.skill-list { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:3px; }
.skill-btn { display:flex; align-items:center; gap:6px; padding:6px 8px; border-radius:6px; cursor:pointer; font-size:12px; color:#374151; }
.skill-btn:hover { background:#e8ecf1; }
.skill-btn.active { background:#1677ff12; color:#1677ff; font-weight:600; }
.skill-btn span { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.multi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:8px; margin-bottom:12px; }
.multi-cell { border:1px solid #e5e7eb; border-radius:8px; padding:8px; }
.multi-label { font-size:11px; color:#1677ff; font-weight:600; margin-bottom:4px; }

@media (max-width:768px) { .teach-panel,.skill-panel { display:none; } .teach-layout { margin:0; } }
</style>
