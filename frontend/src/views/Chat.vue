<template>
  <div class="chat-layout">
    <!-- 左侧：历史对话列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" :icon="Plus" @click="newConv" class="new-chat-btn" size="small">新建对话</el-button>
      </div>
      <div class="conv-list">
        <div v-for="c in convs" :key="c.id" :class="['conv-item',{active:activeConv===c.id}]" @click="switchConv(c)">
          <div class="conv-title">{{ c.title }}</div>
          <div class="conv-time">{{ c.time }}</div>
          <el-button link size="small" class="conv-del" @click.stop="delConv(c)"><el-icon><Delete /></el-icon></el-button>
        </div>
        <div v-if="convs.length===0" style="text-align:center;color:#bbb;padding:20px;font-size:12px">暂无历史对话</div>
      </div>
    </div>

    <!-- 右侧：对话区 -->
    <div class="chat-main">
      <div class="chat-tools">
        <el-radio-group v-model="mode" size="small">
          <el-radio-button value="single">单模型</el-radio-button>
          <el-radio-button value="multi">多模型对比</el-radio-button>
        </el-radio-group>
        <template v-if="mode==='single'">
          <el-select v-model="model" size="small" style="width:120px">
            <el-option v-for="m in modelList" :key="m" :label="m" :value="m" />
          </el-select>
        </template>
        <template v-else>
          <el-select v-model="multiModels" size="small" style="width:240px" multiple collapse-tags>
            <el-option v-for="m in modelList" :key="m" :label="m" :value="m" />
          </el-select>
        </template>
        <el-select v-model="activeSkill" size="small" style="width:140px" placeholder="技能" clearable>
          <el-option v-for="s in skills" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-select v-model="kbId" size="small" style="width:140px" placeholder="知识库" clearable>
          <el-option v-for="k in kbs" :key="k.id" :label="k.name" :value="k.id" />
        </el-select>
      </div>

      <!-- 对话内容 -->
      <div class="chat-body" ref="bodyRef">
        <div v-if="msgs.length===0" class="empty-state">
          <p>输入消息开始与 AI 对话</p>
        </div>
        <template v-if="mode==='single'">
          <div v-for="(m,i) in msgs" :key="i" :class="['msg',m.role]">
            <div class="msg-text" v-html="render(m.content)"></div>
          </div>
        </template>
        <template v-else>
          <div v-for="(m,i) in msgs" :key="i">
            <div v-if="m.role==='user'" class="msg user"><div class="msg-text">{{ m.content }}</div></div>
            <div v-else class="multi-results">
              <div v-for="r in m.results" :key="r.model" class="multi-col">
                <div class="multi-model-label">{{ r.model }}</div>
                <div class="msg-text" v-html="render(r.content)"></div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 输入框 -->
      <div class="chat-input">
        <el-upload :show-file-list="false" :before-upload="handleUpload" accept=".pdf,.docx,.txt,.md,.jpg,.png">
          <el-button circle size="small"><el-icon><UploadFilled /></el-icon></el-button>
        </el-upload>
        <el-input v-model="input" type="textarea" :rows="3" placeholder="输入消息，Enter 发送"
          @keydown.enter.exact.prevent="send(input)" resize="none" />
        <el-button type="primary" @click="send(input)" :loading="thinking" size="small">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, UploadFilled, Delete } from '@element-plus/icons-vue'
import { apiGet, apiDelete } from '../api.js'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'

const route = useRoute()
const input = ref(''), mode = ref('single'), model = ref('deepseek'), multiModels = ref(['deepseek','qwen'])
const activeSkill = ref(''), kbId = ref(''), thinking = ref(false)
const msgs = ref([]), convs = ref([]), activeConv = ref('new')
const skills = ref([]), kbs = ref([])
const modelList = ['deepseek','qwen','zhipu','kimi','minimax','doubao']
const bodyRef = ref(null)

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

function newConv() { activeConv.value = 'new'; msgs.value = [] }
function switchConv(c) {
  activeConv.value = c.id
  // Load messages from this conversation
  loadMessages(c.id)
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
  input.value = ''; thinking.value = true
  await nextTick(); scrollBottom()

  if (mode.value === 'single') {
    msgs.value.push({ role: 'user', content: t.trim() })
    msgs.value.push({ role: 'assistant', content: '' })
    await streamChat(t.trim(), msgs.value[msgs.value.length-1], model.value)
  } else {
    msgs.value.push({ role: 'user', content: t.trim() })
    const resultItems = multiModels.value.map(m => ({ model: m, content: '' }))
    msgs.value.push({ role: 'assistant', results: resultItems })
    await Promise.all(multiModels.value.map((m, i) =>
      streamChat(t.trim(), resultItems[i], m)
    ))
  }
  thinking.value = false
  await nextTick(); scrollBottom()
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
              // Refresh conversation list
              const cdata = await apiGet('/api/chat/conversations')
              if (cdata) convs.value = cdata.map(c => ({id:c.id,title:c.title||c.name||'对话',time:c.created_at?.slice(0,10)||'刚刚'}))
            }
            if (json.content) {
              fullContent += json.content
              if (target.content !== undefined) target.content = fullContent
              else if (target.results) target.content = fullContent
            }
          } catch (e) { /* ignore parse errors for partial chunks */ }
        }
      }
    }
  } catch (e) {
    target.content = `[错误] ${e.message}`
  }
}

function render(text) {
  if (!text) return ''
  // 合并多余换行为最多两个
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
.chat-layout { display:flex; height:calc(100vh - 160px); background:#fff; }
.chat-sidebar { width:200px; min-width:200px; border-right:1px solid #e5e7eb; display:flex; flex-direction:column; }
.sidebar-header { padding:8px; }
.new-chat-btn { width:100%; }
.conv-list { flex:1; overflow-y:auto; padding:0 6px; }
.conv-item { padding:8px 10px; border-radius:6px; cursor:pointer; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center; }
.conv-item:hover,.conv-item.active { background:#f0f5ff; }
.conv-title { font-size:13px; color:#1f2937; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.conv-time { font-size:10px; color:#9ca3af; margin-left:8px; }
.conv-del { opacity:0; }
.conv-item:hover .conv-del { opacity:1; }

.chat-main { flex:1; display:flex; flex-direction:column; min-width:0; }
.chat-tools { padding:6px 12px; border-bottom:1px solid #e5e7eb; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.chat-body { flex:1; overflow-y:auto; padding:12px 24px 12px 24px; }
.empty-state { text-align:center; padding:60px 20px; color:#9ca3af; }
.msg { margin-bottom:12px; }
.msg.user { text-align:right; }
.msg-text { display:inline-block; max-width:80%; padding:8px 12px; border-radius:10px; font-size:13px; line-height:1.6; white-space:pre-wrap; word-break:break-word; }
.msg.user .msg-text { background:#1677ff; color:#fff; }
.msg.assistant .msg-text { background:#f3f4f6; color:#1f2937; }
.msg-text :deep(pre) { background:#1e293b;color:#e2e8f0;padding:6px 10px;border-radius:6px;overflow-x:auto;font-size:12px; }
.msg-text :deep(code) { background:#e5e7eb;padding:1px 3px;border-radius:3px;font-size:12px; }
.multi-results { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap:8px; margin-bottom:12px; }
.multi-col { border:1px solid #e5e7eb; border-radius:8px; padding:8px; }
.multi-model-label { font-size:11px; color:#1677ff; font-weight:600; margin-bottom:6px; }
.chat-input { padding:8px 12px; border-top:1px solid #e5e7eb; display:flex; gap:8px; align-items:center; }
.chat-input :deep(.el-textarea__inner) { border-radius:8px; font-size:13px; padding:6px 10px; }
</style>
