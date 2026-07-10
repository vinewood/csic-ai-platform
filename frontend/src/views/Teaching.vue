<template>
  <div class="teach-layout">
    <!-- 左栏：教学功能 + 历史 -->
    <div class="teach-panel">
      <el-button type="primary" :icon="Plus" size="small" class="new-btn" @click="newConv">新建对话</el-button>

      <div class="panel-title" style="margin-top:12px">教学功能</div>
      <div class="func-list">
        <div v-for="f in teachFuncs" :key="f.id" class="func-btn" :class="{active:f.id===funcId}" @click="funcId=f.id;input=f.prompt">
          <el-icon :size="15"><component :is="f.icon" /></el-icon>{{ f.label }}
        </div>
      </div>

      <div class="panel-divider"></div>
      <div class="panel-title">历史对话</div>
      <div class="hist-list">
        <div v-for="c in convs" :key="c.id" class="hist-item" :class="{active:c.id===convId}" @click="loadConv(c)">
          <span class="hist-title">{{ c.title || '对话' }}</span>
          <span class="hist-time">{{ c.time }}</span>
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
            <el-option v-for="m in models" :key="m" :label="m" :value="m" />
          </el-select>
        </template>
        <template v-else>
          <el-select v-model="multiModels" size="small" style="width:200px" multiple collapse-tags>
            <el-option v-for="m in models" :key="m" :label="m" :value="m" />
          </el-select>
        </template>
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
        <div v-for="(m,i) in msgs" :key="i" :class="['msg',m.role]">
          <div class="msg-text" v-html="render(m.content)"></div>
        </div>
        <div v-if="thinking" class="msg assistant"><div class="msg-text">...</div></div>
      </div>

      <!-- 输入区 -->
      <div class="chat-input">
        <el-upload :show-file-list="false" :before-upload="handleUpload" accept=".pdf,.docx,.txt,.md">
          <el-button circle size="small"><el-icon><UploadFilled /></el-icon></el-button>
        </el-upload>
        <el-input v-model="input" type="textarea" :rows="3" placeholder="输入教学需求，Enter 发送"
          @keydown.enter.exact.prevent="doSend" resize="none" />
        <el-button type="primary" @click="doSend" :loading="thinking" size="small">发送</el-button>
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
import { Plus, UploadFilled, EditPen, Document, DataBoard, Notebook, MagicStick } from '@element-plus/icons-vue'
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

const input = ref(''), mode = ref('single'), model = ref('deepseek'), multiModels = ref(['deepseek','qwen'])
const thinking = ref(false), msgs = ref([]), skillId = ref(''), funcId = ref('')
const skills = ref([]), convs = ref([]), convId = ref('new')
const models = ['deepseek','qwen','zhipu','kimi','minimax','doubao']
const bodyRef = ref(null)

onMounted(async () => {
  const [s, c] = await Promise.all([apiGet('/api/skills'), apiGet('/api/chat/conversations')])
  if (s) skills.value = s
  if (c) convs.value = c.map(x => ({ id:x.id, title:x.title||'对话', time:x.created_at?.slice(0,10)||'' }))
})

function newConv() { convId.value = 'new'; msgs.value = [] }
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
  const lastAssistant = [...msgs.value].reverse().find(m => m.role === 'assistant')
  if (!lastAssistant) { ElMessage.warning('暂无可保存的内容'); return }
  // 尝试解析 JSON 课题并保存到教学课题表
  try {
    const match = lastAssistant.content.match(/\[[\s\S]*\]/)
    if (match) {
      const topics = JSON.parse(match[0])
      for (const t of topics) {
        await apiGet(`/api/teaching/save-topic?title=${encodeURIComponent(t.title||'')}&desc=${encodeURIComponent(t.desc||t.description||'')}&level=${encodeURIComponent(t.level||'标准')}&hours=${t.hours||4}`)
      }
      ElMessage.success(`已保存${topics.length}个课题`)
      return
    }
  } catch {}
  ElMessage.success('对话内容已保存（可在历史对话中查看）')
}

async function doSend() {
  const t = input.value.trim()
  if (!t || thinking.value) return
  input.value = ''; thinking.value = true; funcId.value = ''
  msgs.value.push({ role: 'user', content: t })
  await nextTick(); scrollBottom()
  msgs.value.push({ role: 'assistant', content: '' })
  const last = msgs.value[msgs.value.length - 1]

  const token = localStorage.getItem('csic_token')
  const API_BASE = location.port === '5173' ? 'http://localhost:8000' : ''
  try {
    const resp = await fetch(`${API_BASE}/api/chat/dify-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ query: t, model: model.value, skill_id: skillId.value || '' })
    })
    const reader = resp.body.getReader()
    const dec = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      for (const line of dec.decode(value, { stream: true }).split('\n')) {
        if (line.startsWith('data: ')) {
          const d = line.slice(6)
          if (d === '[DONE]') continue
          try { const j = JSON.parse(d); if (j.content) last.content += j.content
            if (j.conversation_id && convId.value === 'new') { convId.value = j.conversation_id; refreshConvs() }
          } catch {}
        }
      }
    }
  } catch (e) { last.content = `[错误] ${e.message}` }
  finally { thinking.value = false; await nextTick(); scrollBottom() }
}

function render(t) {
  if (!t) return ''
  try { return marked.parse(t.replace(/\n{3,}/g, '\n\n')) } catch { return t }
}
function scrollBottom() { nextTick(() => { if(bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight }) }

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

.chat-input { padding:8px 12px; border-top:1px solid #e5e7eb; display:flex; gap:6px; align-items:center; }
.chat-input :deep(.el-textarea__inner) { border-radius:8px; font-size:13px; padding:6px 8px; }

.skill-panel { width:160px; min-width:160px; background:#f8f9fb; border-left:1px solid #e5e7eb; padding:10px 8px; }
.skill-list { display:flex; flex-direction:column; gap:3px; }
.skill-btn { display:flex; align-items:center; gap:6px; padding:6px 8px; border-radius:6px; cursor:pointer; font-size:12px; color:#374151; }
.skill-btn:hover { background:#e8ecf1; }
.skill-btn.active { background:#1677ff12; color:#1677ff; font-weight:600; }
.skill-btn span { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

@media (max-width:768px) { .teach-panel,.skill-panel { display:none; } .teach-layout { margin:0; } }
</style>
