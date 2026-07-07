<template>
  <div class="chat-layout">
    <!-- 左侧：历史对话列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" size="default" :icon="Plus" @click="newConversation" class="new-chat-btn">新建对话</el-button>
      </div>

      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['conv-item', { active: currentConv === conv.id }]"
          @click="switchConv(conv.id)"
        >
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-meta">{{ conv.model }} · {{ conv.time }}</div>
        </div>
      </div>

      <!-- 底部快捷操作 -->
      <div class="sidebar-footer">
        <el-button text size="small" :icon="Delete" @click="clearAll">清空对话</el-button>
      </div>
    </div>

    <!-- 右侧：对话区 -->
    <div class="chat-main">
      <!-- 工具栏 -->
      <el-card shadow="never" class="toolbar-card">
        <div class="chat-toolbar">
          <el-radio-group v-model="mode" size="small">
            <el-radio-button value="single">单模型</el-radio-button>
            <el-radio-button value="multi">多模型</el-radio-button>
          </el-radio-group>

          <el-select v-if="mode === 'single'" v-model="activeModel" size="default" style="width:170px;">
            <el-option v-for="m in models" :key="m.id" :label="m.label" :value="m.id">
              <span class="model-dot" :style="{background:m.color}"></span> {{ m.label }}
            </el-option>
          </el-select>
          <!-- 多模型：芯片式标签 + 平铺切换 -->
          <template v-else>
            <div class="multi-chip-wrap">
              <div class="chip-list">
                <div
                  v-for="mId in multiModels"
                  :key="mId"
                  :class="['model-chip', { active: multiLayout === 'tab' && activeTabModel === mId }]"
                  @click="multiLayout = 'tab'; activeTabModel = mId"
                >
                  <span class="model-dot" :style="{background:getModelColor(mId)}"></span>
                  <span class="chip-label">{{ getModelName(mId) }}</span>
                  <el-icon class="chip-close" @click.stop="removeTab(mId)"><Close /></el-icon>
                </div>
                <!-- 添加按钮 -->
                <el-popover placement="bottom" :width="180" trigger="click" popper-class="model-add-popover">
                  <template #reference>
                    <div class="model-chip chip-add">+</div>
                  </template>
                  <div v-for="m in availableModels" :key="m.id" class="add-option" @click="addModel(m.id)">
                    <span class="model-dot" :style="{background:m.color}"></span>
                    {{ m.label }}
                  </div>
                  <div v-if="!availableModels.length" style="color:#94a3b8;font-size:12px;text-align:center;padding:8px 0;">
                    已添加全部模型
                  </div>
                </el-popover>
              </div>
              <el-button-group size="small" style="flex-shrink:0;">
                <el-button :type="multiLayout==='tab'?'primary':'default'" :icon="List" @click="multiLayout='tab'" />
                <el-button :type="multiLayout==='tile'?'primary':'default'" :icon="Grid" @click="multiLayout='tile'" />
              </el-button-group>
            </div>
          </template>

          <!-- 技能选择（仅收藏的技能） -->
          <el-select v-model="activeSkill" placeholder="技能" size="default" style="width:130px;" clearable>
            <el-option v-for="s in favoritedSkills" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>

          <!-- 知识库选择 -->
          <el-select v-model="activeKb" placeholder="知识库" size="default" style="width:130px;" clearable>
            <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>

          <!-- 附件上传 -->
          <el-upload :auto-upload="false" :show-file-list="false" @change="onFileAdd">
            <el-button size="default" :icon="Paperclip" circle />
          </el-upload>

          <!-- 模型参数 -->
          <el-popover placement="bottom" :width="260" trigger="click">
            <template #reference>
              <el-button size="default" :icon="Setting" circle />
            </template>
            <div style="padding:4px 0;">
              <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#4b5563;">
                  <span>温度 (Temperature)</span><span>{{ params.temperature.toFixed(1) }}</span>
                </div>
                <el-slider v-model="params.temperature" :min="0" :max="2" :step="0.1" size="small" />
              </div>
              <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#4b5563;">
                  <span>Top-P</span><span>{{ params.topP.toFixed(1) }}</span>
                </div>
                <el-slider v-model="params.topP" :min="0" :max="1" :step="0.05" size="small" />
              </div>
              <div>
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#4b5563;">
                  <span>最大 Token</span><span>{{ params.maxTokens }}</span>
                </div>
                <el-slider v-model="params.maxTokens" :min="512" :max="8192" :step="512" size="small" />
              </div>
            </div>
          </el-popover>
        </div>
      </el-card>

      <!-- 多模型：平铺模式 -->
      <div v-if="mode === 'multi' && multiLayout === 'tile'" class="multi-tile-wrap">
        <div v-for="mId in multiModels" :key="mId" class="tile-col">
          <div class="tile-header">
            <span class="model-dot" :style="{background:getModelColor(mId)}"></span>
            {{ getModelName(mId) }}
            <el-button link size="small" :icon="Close" style="margin-left:auto;" @click="removeTab(mId)" />
          </div>
          <div class="tile-body">
            <div v-for="(msg, i) in (multiMsgs[mId] || [])" :key="i" :class="['tile-msg', msg.role]">
              <div class="tile-msg-text">{{ msg.content }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 多模型：Tab模式（每次只显示当前选中的模型） -->
      <div v-if="mode === 'multi' && multiLayout === 'tab'" class="single-model-chat">
        <div v-if="activeTabModel && multiMsgs[activeTabModel]?.length" class="multi-tab-msgs">
          <div v-for="(msg, i) in multiMsgs[activeTabModel]" :key="i" :class="['msg-row', msg.role]">
            <div class="msg-bubble" :style="msg.role === 'assistant' ? {background:'#f3f4f6',color:'#1a1a2e'} : {background:'#1677ff',color:'#fff'}">
              <div class="msg-label">{{ msg.role === 'user' ? '我' : getModelName(activeTabModel) }}</div>
              <div class="msg-content">{{ msg.content }}</div>
            </div>
          </div>
        </div>
        <div v-else class="msg-empty" style="flex:1;">
          <div class="empty-icon-inner">
            <el-icon :size="36" color="#1677ff"><ChatDotRound /></el-icon>
          </div>
          <h4>多模型对话 — {{ getModelName(activeTabModel) }}</h4>
          <p>在下方输入问题，发送后该模型将回复</p>
        </div>
      </div>

      <!-- 单模型消息列表 -->
      <div v-if="mode === 'single'" class="msg-list" ref="msgListRef">
        <div v-if="!msgs.length" class="msg-empty">
          <div class="empty-icon-inner">
            <el-icon :size="36" color="#1677ff"><ChatDotRound /></el-icon>
          </div>
          <h4>开始新对话</h4>
          <p>{{ activeSkill ? '已选择技能: ' + getSkillName(activeSkill) : '选择模型，输入问题开始' }}</p>
          <div v-if="!attachments.length" class="empty-tips">
            <el-button v-for="p in prompts" :key="p.key" size="small" round @click="quickSend(p.text)">{{ p.label }}</el-button>
          </div>
        </div>
        <template v-for="(msg, i) in msgs" :key="i">
          <div :class="['msg-row', msg.role]">
            <div class="msg-bubble" :style="msg.role === 'assistant' ? {background:'#f3f4f6',color:'#1a1a2e'} : {background:'#1677ff',color:'#fff'}">
              <div class="msg-label">{{ msg.role === 'user' ? '我' : getModelName(msg.model || activeModel) }}</div>
              <div class="msg-content">{{ msg.content }}</div>
            </div>
          </div>
        </template>
      </div>

      <!-- 附件列表 -->
      <div v-if="attachments.length" class="attach-bar">
        <el-tag v-for="(f, i) in attachments" :key="i" closable @close="attachments.splice(i,1)" size="small">
          <el-icon style="margin-right:4px;"><Paperclip /></el-icon>{{ f.name }}
        </el-tag>
      </div>

      <!-- 发送区 -->
      <div class="sender-wrap">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="输入问题，Enter 发送..."
          @keydown.enter.prevent="sendMessage"
          :disabled="sending"
        />
        <div class="sender-actions">
          <span class="skill-tag" v-if="activeSkill">
            <el-tag size="small" closable @close="activeSkill=''">{{ getSkillName(activeSkill) }}</el-tag>
          </span>
          <el-button type="primary" @click="sendMessage" :loading="sending" :icon="Promotion">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, Delete, Paperclip, Promotion, ChatDotRound, Setting, Close, List, Grid } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

// ---- API 配置 ----
const API_BASE = 'http://localhost:8000'
function getToken() { return localStorage.getItem('csic_token') || '' }
function authHeaders() {
  const t = getToken()
  return t ? { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }
}
async function apiPost(path, data) {
  try {
    const resp = await fetch(API_BASE + path, { method: 'POST', headers: authHeaders(), body: JSON.stringify(data) })
    if (resp.status === 401) { router.push('/'); return null }
    return resp.ok ? await resp.json() : null
  } catch { return null }
}
async function apiGet(path) {
  try {
    const resp = await fetch(API_BASE + path, { headers: authHeaders() })
    if (resp.status === 401) { router.push('/'); return null }
    return resp.ok ? await resp.json() : null
  } catch { return null }
}

const models = [
  { id: 'qwen', label: '千问', color: '#1677ff' },
  { id: 'zhipu', label: '智谱', color: '#5b4cc4' },
  { id: 'minimax', label: 'MiniMax', color: '#10b981' },
  { id: 'doubao', label: '豆包', color: '#8b5cf6' },
  { id: 'deepseek', label: 'DeepSeek', color: '#4a6cf7' },
  { id: 'kimi', label: 'Kimi', color: '#f59e0b' }
]

const skills = ref([])
const favoritedSkills = computed(() => skills.value.filter(s => s.favorited))

// 多模型 Tab 功能
const availableModels = computed(() => models.filter(m => !multiModels.value.includes(m.id)))

function addModel(id) {
  if (!id || multiModels.value.includes(id)) return
  multiModels.value.push(id)
  activeTabModel.value = id
  addModelId.value = ''
  // 关闭 popover（点击 body 触发关闭）
  document.body.click()
}
function removeTab(id) {
  const idx = multiModels.value.indexOf(id)
  multiModels.value = multiModels.value.filter(m => m !== id)
  if (activeTabModel.value === id) {
    activeTabModel.value = multiModels.value[Math.min(idx, multiModels.value.length - 1)] || ''
  }
}

// 知识库
const kbs = ref([
  { id: 'kb1', name: '党校教学资料库', docs: 156 },
  { id: 'kb2', name: '党建研究成果', docs: 89 },
  { id: 'kb3', name: '政策法规库', docs: 234 }
])

const prompts = [
  { key: '1', label: '分析党建课题', text: '分析基层党建研究课题的选题方向' },
  { key: '2', label: '设计培训大纲', text: '设计一堂党的二十大精神解读培训课程大纲' },
  { key: '3', label: '润色论文摘要', text: '请帮我润色以下论文摘要' },
  { key: '4', label: '总结新闻', text: '总结中国船舶行业最新动态' }
]

// 对话状态
const mode = ref('single')
const activeModel = ref('qwen')
const multiModels = ref(['qwen', 'zhipu', 'minimax', 'doubao'])
const activeTabModel = ref('qwen')
const multiLayout = ref('tab')
const addModelId = ref('')
const activeSkill = ref('')
const activeKb = ref('')
const inputText = ref('')
const sending = ref(false)

// 模型参数
const params = reactive({ temperature: 0.7, topP: 0.9, maxTokens: 2048 })

const msgs = ref([])
const multiMsgs = reactive({})
const attachments = ref([])
const msgListRef = ref(null)

// 从后端加载数据
onMounted(async () => {
  // 尝试从后端加载对话历史和模型
  const convs = await apiGet('/api/chat/conversations')
  if (convs && convs.length) {
    conversations.value = convs.map(c => ({ id: c.id, title: c.name || c.title || '对话', model: c.model || getModelName(activeModel.value), time: c.created_at || '刚刚' }))
  }
  const modelData = await apiGet('/api/chat/models')
  if (modelData && modelData.models) {
    const oldColors = Object.fromEntries(models.map(m => [m.id, m.color]))
    models.length = 0
    modelData.models.forEach(m => { m.color = oldColors[m.id] || m.color || '#999'; models.push(m) })
  }
  // 从后端加载技能（替换硬编码列表）
  const skillData = await apiGet('/api/skills')
  if (skillData) {
    skills.value = skillData.map(s => ({ id: s.id, name: s.name, favorited: s.favorited, desc: s.desc }))
    // 如果 URL 参数指定了技能，检查是否存在
    const skillId = route.query.skill
    if (skillId && skills.value.some(s => s.id === skillId)) {
      activeSkill.value = skillId
      ElMessage.success('已挂载技能: ' + getSkillName(skillId))
    }
  }
})

// 历史对话
const currentConv = ref('conv_1')
let convIdCounter = 2
const conversations = ref([
  { id: 'conv_1', title: '党建课题分析', model: 'DeepSeek V3', time: '今天 14:20' },
  { id: 'conv_2', title: '论文摘要润色', model: '通义千问 Max', time: '今天 11:05' },
  { id: 'conv_3', title: '培训大纲设计', model: '通义千问 Plus', time: '昨天 16:30' },
  { id: 'conv_4', title: '船舶行业动态', model: 'Kimi', time: '昨天 09:15' }
])

function getModelName(id) { return models.find(m => m.id === id)?.label || id }
function getModelColor(id) { return models.find(m => m.id === id)?.color || '#999' }
function getSkillName(id) { return (skills.value || []).find(s => s.id === id)?.name || id || '技能' }

function newConversation() {
  const id = 'conv_' + convIdCounter++
  conversations.value.unshift({ id, title: '新对话', model: getModelName(activeModel.value), time: '刚刚' })
  currentConv.value = id
  msgs.value = []
  inputText.value = ''
}

function switchConv(id) {
  currentConv.value = id
  // 实际从后端加载对话记录
  msgs.value = []
  ElMessage.info('已切换对话')
}

function clearAll() {
  conversations.value = []
  msgs.value = []
  ElMessage.success('已清空')
}

function onFileAdd(file) {
  attachments.value.push({ name: file.name, raw: file.raw })
  // 尝试上传到后端
  const formData = new FormData()
  formData.append('file', file.raw)
  fetch(API_BASE + '/api/files/upload', { method: 'POST', headers: { 'Authorization': 'Bearer ' + getToken() }, body: formData })
    .then(r => r.json()).then(d => { if (d.url) ElMessage.success('已上传: ' + file.name) }).catch(() => {})
  ElMessage.success('已添加附件: ' + file.name)
}

function quickSend(text) { inputText.value = text; sendMessage() }

function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  if (mode.value === 'single') {
    msgs.value.push({ role: 'user', content: text, model: activeModel.value })
    inputText.value = ''
    sending.value = true
    const aiMsg = { role: 'assistant', content: '', model: activeModel.value, streaming: true }
    msgs.value.push(aiMsg)

    // 尝试调用后端 SSE
    const token = getToken()
    if (token) {
      fetch(API_BASE + '/api/chat/stream', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text, model: activeModel.value,
          conversation_id: currentConv.value.startsWith('conv_') ? '' : currentConv.value,
          temperature: params.temperature, top_p: params.topP, max_tokens: params.maxTokens,
        })
      }).then(async (resp) => {
        if (!resp.ok) { throw new Error('API error') }
        const reader = resp.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          for (const line of lines) {
            if (line.startsWith('data: ') && line !== 'data: [DONE]') {
              try {
                const d = JSON.parse(line.slice(6))
                aiMsg.content += d.answer || ''
                nextTick(() => { msgListRef.value?.scrollTo({ top: msgListRef.value.scrollHeight, behavior: 'smooth' }) })
              } catch {}
            }
          }
        }
        aiMsg.streaming = false; sending.value = false
      }).catch(() => {
        // 后端不可用，回退到 mock
        const fullText = '这是 AI 的智能回复（后端未连接，使用本地模拟）。\n\n模型：' + getModelName(activeModel.value) + '\n\n请确保后端服务已启动：cd backend && uvicorn app.main:app --reload --port 8000'
        let idx = 0
        const timer = setInterval(() => {
          if (idx >= fullText.length) { aiMsg.streaming = false; sending.value = false; clearInterval(timer); return }
          aiMsg.content += fullText[idx]; idx++
          nextTick(() => { msgListRef.value?.scrollTo({ top: msgListRef.value.scrollHeight, behavior: 'smooth' }) })
        }, 30)
      })
    } else {
      // 无 token，回退 mock
      const fullText = '这是 AI 的智能回复（演示模式）。\n\n请通过登录页登录后即可连接后端。'
      let idx = 0
      const timer = setInterval(() => {
        if (idx >= fullText.length) { aiMsg.streaming = false; sending.value = false; clearInterval(timer); return }
        aiMsg.content += fullText[idx]; idx++
        nextTick(() => { msgListRef.value?.scrollTo({ top: msgListRef.value.scrollHeight, behavior: 'smooth' }) })
      }, 30)
    }
  } else {
    // 多模型模式
    inputText.value = ''
    sending.value = true
    let completedCount = 0
    const targetModels = multiLayout.value === 'tab' ? [activeTabModel.value] : multiModels.value
    targetModels.forEach(mId => {
      if (!multiMsgs[mId]) multiMsgs[mId] = []
      multiMsgs[mId].push({ role: 'user', content: text })
      const ai = { role: 'assistant', content: '', streaming: true }
      multiMsgs[mId].push(ai)
      const reply = `[${getModelName(mId)}] 智能回复内容。连接后端后将展示每个模型的独立回复。`
      let idx = 0
      const timer = setInterval(() => {
        if (idx >= reply.length) { ai.streaming = false; completedCount++; if (completedCount === targetModels.length) sending.value = false; clearInterval(timer); return }
        ai.content += reply[idx]; idx++
      }, 15)
    })
  }
}
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 148px);
  gap: 12px;
}

/* 左侧栏 */
.chat-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 14px;
  border-bottom: 1px solid var(--border-color);
}
.new-chat-btn { width: 100%; }

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}

.conv-item {
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 6px;
  margin-bottom: 2px;
  transition: all .15s;
}
.conv-item:hover { background: #f6f8fa; }
.conv-item.active { background: #f0f5ff; border: 1px solid #bae0ff; }
.conv-title { font-size: 13px; font-weight: 600; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-meta { font-size: 11px; color: #94a3b8; margin-top: 3px; }

.sidebar-footer { padding: 10px 14px; border-top: 1px solid var(--border-color); }

/* 右侧主区 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.toolbar-card {
  flex-shrink: 0;
  margin-bottom: 8px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 6px 0;
}
.chat-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.model-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.model-checks :deep(.el-checkbox__inner) { width: 18px; height: 18px; }
.model-checks :deep(.el-checkbox__label) { font-size: 13px; }

/* 消息列表 */
.msg-list {
  flex: 1;
  overflow-y: auto;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 16px;
  margin-bottom: 8px;
}

.msg-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  min-height: 300px; text-align: center;
}
.empty-icon-inner {
  width: 70px; height: 70px;
  border-radius: 50%;
  background: #f0f5ff;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 14px;
}
.msg-empty h4 { margin: 0 0 4px; color: var(--text-main); font-size: 16px; }
.msg-empty p { color: #94a3b8; font-size: 13px; margin: 0 0 16px; }
.empty-tips { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }

.msg-row { margin-bottom: 14px; }
.msg-row.user { text-align: right; }
.msg-bubble {
  display: inline-block;
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 10px;
  text-align: left;
  line-height: 1.6;
}
.msg-label { font-size: 11px; font-weight: 600; margin-bottom: 4px; opacity: 0.75; }
.msg-content { font-size: 14px; white-space: pre-wrap; }

/* 多模型 */
.multi-chat-wrap {
  display: flex;
  gap: 8px;
  flex: 1;
  min-height: 0;
  margin-bottom: 8px;
}
.multi-col {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  font-size: 12px;
  font-weight: 600;
  background: #f8fafc;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 6px;
}
.multi-col-body {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
.multi-msg { margin-bottom: 8px; }
.multi-msg.user .multi-msg-text { background: #1677ff; color: #fff; display:inline-block; padding:8px 12px; border-radius:8px; font-size:13px; }
.multi-msg.assistant .multi-msg-text { background:#f3f4f6; color:#1a1a2e; display:inline-block; padding:8px 12px; border-radius:8px; font-size:13px; }

/* 附件 */
.attach-bar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 6px 0;
}
.attach-bar .el-tag { margin: 0; }

/* 发送区 */
.sender-wrap {
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 10px;
}
.sender-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.skill-tag { margin-right: auto; }

/* 多模型芯片标签 */
.multi-chip-wrap { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.chip-list { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.model-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 8px 4px 10px;
  border-radius: 20px; font-size: 12px; font-weight: 500;
  background: #f3f4f6; border: 1px solid #e5e7eb;
  cursor: pointer; transition: all .15s; user-select: none;
}
.model-chip:hover { border-color: #bae0ff; background: #f0f5ff; }
.model-chip.active { background: #1677ff; color: #fff; border-color: #1677ff; }
.model-chip.active .chip-close { color: rgba(255,255,255,0.7); }
.model-chip.active .chip-close:hover { color: #fff; }
.chip-label { line-height: 1; }
.chip-close { font-size: 12px; color: #9ca3af; cursor: pointer; margin-left: 2px; }
.chip-close:hover { color: #ef4444; }
.chip-add {
  background: #fff; color: #1677ff; font-weight: 700; font-size: 16px;
  padding: 4px 12px; border: 1px dashed #bae0ff;
}
.chip-add:hover { background: #f0f5ff; }

.model-add-popover { padding: 4px; }
.add-option {
  padding: 8px 12px; cursor: pointer; border-radius: 6px;
  font-size: 13px; display: flex; align-items: center; gap: 6px;
  transition: background .15s;
}
.add-option:hover { background: #f0f5ff; }

/* 平铺模式 */
.multi-tile-wrap { display: flex; gap: 8px; flex: 1; min-height: 0; margin-bottom: 8px; }
.tile-col { flex: 1; background: #fff; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; overflow: hidden; }
.tile-header { padding: 8px 12px; font-size: 12px; font-weight: 600; background: #f8fafc; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 6px; }
.tile-body { flex: 1; overflow-y: auto; padding: 10px; }
.tile-msg { margin-bottom: 8px; }
.tile-msg.user .tile-msg-text { background: #1677ff; color: #fff; display:inline-block; padding:8px 12px; border-radius:8px; font-size:13px; }
.tile-msg.assistant .tile-msg-text { background:#f3f4f6; color:#1a1a2e; display:inline-block; padding:8px 12px; border-radius:8px; font-size:13px; }

/* Tab模式消息区 */
.single-model-chat { flex:1; display:flex; flex-direction:column; background:#fff; border-radius:8px; border:1px solid var(--border-color); padding:16px; margin-bottom:8px; overflow-y:auto; }
.multi-tab-msgs { flex:1; }
.multi-tab-msgs .msg-row { margin-bottom:14px; }
.multi-tab-msgs .msg-row.user { text-align:right; }
.multi-tab-msgs .msg-bubble { display:inline-block; max-width:75%; padding:10px 14px; border-radius:10px; text-align:left; line-height:1.6; }

@media (max-width: 768px) {
  .chat-sidebar { display: none; }
  .chat-layout { height: calc(100vh - 104px); }
}
</style>
