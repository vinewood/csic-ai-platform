<template>
  <div class="academic-workspace">
    <!-- Hero header — keep style -->
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1532619675605-1ede6c2ed2b0?w=1200&q=80);">
      <div class="hero-content">
        <h2>科研工作台</h2>
        <p>AI 驱动的学术研究助手 · 基于 gpt_academic 引擎</p>
      </div>
    </div>

    <!-- Main workspace: left plugins + right chat -->
    <div class="workspace-container">
      <!-- ====== LEFT: 功能插件面板 ====== -->
      <div class="plugin-panel">
        <div class="panel-title">功能插件</div>
        
        <div class="plugin-group">
          <div class="group-label">学术写作</div>
          <div v-for="p in writingPlugins" :key="p.id" 
            class="plugin-btn" :class="{ active: activePlugin === p.id }"
            @click="activatePlugin(p)">
            <el-icon :size="18"><component :is="p.icon" /></el-icon>
            <span>{{ p.label }}</span>
          </div>
        </div>

        <div class="plugin-group">
          <div class="group-label">论文处理</div>
          <div v-for="p in paperPlugins" :key="p.id" 
            class="plugin-btn" :class="{ active: activePlugin === p.id }"
            @click="activatePlugin(p)">
            <el-icon :size="18"><component :is="p.icon" /></el-icon>
            <span>{{ p.label }}</span>
          </div>
        </div>

        <div class="plugin-group">
          <div class="group-label">研究辅助</div>
          <div v-for="p in auxPlugins" :key="p.id" 
            class="plugin-btn" :class="{ active: activePlugin === p.id }"
            @click="activatePlugin(p)">
            <el-icon :size="18"><component :is="p.icon" /></el-icon>
            <span>{{ p.label }}</span>
          </div>
        </div>

        <div class="panel-divider"></div>
        
        <div class="model-selector">
          <span class="model-label">模型</span>
          <el-select v-model="selectedModel" size="small" style="width:100%">
            <el-option label="DeepSeek V3" value="deepseek" />
            <el-option label="千问 Max" value="qwen" />
            <el-option label="智谱 GLM-4" value="zhipu" />
          </el-select>
        </div>

        <div class="param-row">
          <span>Temperature</span>
          <el-slider v-model="temperature" :min="0" :max="2" :step="0.1" size="small" show-input />
        </div>
      </div>

      <!-- ====== RIGHT: 对话工作区 ====== -->
      <div class="chat-area">
        <!-- 对话历史 -->
        <div class="chat-messages" ref="msgBox">
          <div v-if="messages.length === 0" class="welcome-area">
            <div class="welcome-icon">
              <el-icon :size="48"><Reading /></el-icon>
            </div>
            <h3>gpt_academic 科研助手</h3>
            <p>选择一个功能插件开始，或直接在下方输入研究问题</p>
            <div class="quick-actions">
              <el-button v-for="q in quickStarts" :key="q.id" size="small" round @click="quickStart(q)">
                {{ q.label }}
              </el-button>
            </div>
          </div>

          <div v-for="(msg, idx) in messages" :key="idx" class="msg-item" :class="msg.role">
            <div class="msg-avatar">
              <el-icon :size="20"><component :is="msg.role === 'user' ? UserFilled : Cpu" /></el-icon>
            </div>
            <div class="msg-content">
              <div class="msg-text" v-html="renderMarkdown(msg.content)"></div>
              <div class="msg-ops" v-if="msg.role === 'assistant' && msg.content">
                <el-button link size="small" @click="copyText(msg.content)"><el-icon><CopyDocument /></el-icon></el-button>
                <el-button link size="small" @click="regenerate(msg)"><el-icon><Refresh /></el-icon></el-button>
              </div>
            </div>
          </div>

          <div v-if="loading" class="msg-item assistant">
            <div class="msg-avatar"><el-icon :size="20"><Cpu /></el-icon></div>
            <div class="msg-content">
              <div class="thinking-dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="plugin-hint" v-if="activePlugin">
            <el-tag type="primary" size="small" closable @close="activePlugin = null">{{ pluginLabel }}</el-tag>
            <span class="hint-text">{{ pluginHint }}</span>
          </div>

          <div class="input-row">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="3"
              :placeholder="inputPlaceholder"
              resize="none"
              @keydown.enter.ctrl="sendMessage"
            />
          </div>

          <div class="action-bar">
            <div class="left-actions">
              <el-upload
                :show-file-list="false"
                :before-upload="handleUpload"
                accept=".pdf,.docx,.txt,.md"
              >
                <el-button circle size="small"><el-icon><UploadFilled /></el-icon></el-button>
              </el-upload>
              <el-button link size="small" @click="clearChat" :disabled="messages.length === 0">
                <el-icon><Delete /></el-icon> 清空对话
              </el-button>
            </div>
            <div class="right-actions">
              <el-button @click="inputText = ''; activePlugin = null" :disabled="!inputText && !activePlugin">取消</el-button>
              <el-button type="primary" @click="sendMessage" :loading="loading" :disabled="!inputText.trim()">
                <el-icon><Promotion /></el-icon> 发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { 
  Reading, Cpu, UserFilled, Promotion, CopyDocument, Refresh, Delete, UploadFilled,
  EditPen, Document, DataAnalysis, Notebook, MagicStick, Files, Connection, TrendCharts
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPost, apiPut, apiUpload } from '../api.js'
import { marked } from 'marked'

// ====== 功能插件定义 ======
const writingPlugins = [
  { id: 'topics', label: '课题选题生成', icon: MagicStick, hint: '输入研究方向，AI 生成规范的学术选题', placeholder: '请输入您的研究方向或领域，例如：基层党建数字化转型、船舶智能制造...' },
  { id: 'evaluate', label: '选题测评', icon: DataAnalysis, hint: '对已有选题进行四维度综合评估', placeholder: '请输入您要评估的选题名称' },
  { id: 'outline', label: '论文大纲生成', icon: Document, hint: '为研究课题生成完整的论文大纲', placeholder: '请输入论文主题，如：国有企业数字化转型路径研究' },
]

const paperPlugins = [
  { id: 'review', label: '文献综述', icon: Files, hint: '基于主题生成规范的文献综述', placeholder: '请输入文献综述的主题或关键词' },
  { id: 'translate', label: '论文翻译', icon: Connection, hint: '学术论文中英互译，保持专业术语', placeholder: '请粘贴需要翻译的文本，或描述翻译需求' },
  { id: 'polish', label: '论文润色', icon: EditPen, hint: '优化论文表达，修正语法错误', placeholder: '请粘贴需要润色的论文段落' },
]

const auxPlugins = [
  { id: 'chat', label: '学术对话', icon: TrendCharts, hint: '自由提问，AI 助手提供学术建议', placeholder: '请输入您的研究问题...' },
  { id: 'note', label: '会议纪要', icon: Notebook, hint: '将研究讨论转为结构化纪要', placeholder: '请粘贴会议或讨论的文字记录' },
]

const allPlugins = [...writingPlugins, ...paperPlugins, ...auxPlugins]

const quickStarts = [
  { id: 'q1', label: '帮我生成3个党建研究选题', prompt: '请帮我生成3个关于新时代党建工作的研究选题' },
  { id: 'q2', label: '船舶工业高质量发展选题', prompt: '请为船舶工业高质量发展领域生成4个学术选题' },
  { id: 'q3', label: '选题测评示例', prompt: '请评估选题"人工智能赋能基层党建创新路径研究"的学术价值' },
  { id: 'q4', label: '文献综述示例', prompt: '请为主题"数字政府建设与治理现代化"撰写文献综述' },
]

// ====== 状态 ======
const messages = ref([])
const inputText = ref('')
const activePlugin = ref(null)
const loading = ref(false)
const selectedModel = ref('deepseek')
const temperature = ref(0.7)
const msgBox = ref(null)

// ====== 计算属性 ======
const pluginLabel = computed(() => {
  const p = allPlugins.find(p => p.id === activePlugin.value)
  return p ? p.label : ''
})
const pluginHint = computed(() => {
  const p = allPlugins.find(p => p.id === activePlugin.value)
  return p ? p.hint : ''
})
const inputPlaceholder = computed(() => {
  const p = allPlugins.find(p => p.id === activePlugin.value)
  return p ? p.placeholder : '输入您的研究问题，按 Ctrl+Enter 发送...'
})

// ====== 激活插件 ======
function activatePlugin(plugin) {
  activePlugin.value = plugin.id
  inputText.value = ''
}

// ====== 快速开始 ======
function quickStart(q) {
  inputText.value = q.prompt
  activePlugin.value = null
  sendMessage()
}

// ====== 发送消息 ======
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  const plugin = allPlugins.find(p => p.id === activePlugin.value)
  const title = plugin ? plugin.label : '学术助手'

  messages.value.push({ role: 'user', content: text, title })
  inputText.value = ''
  loading.value = true
  
  await nextTick()
  scrollBottom()

  try {
    // 路由到对应 API
    const endpoint = getEndpoint(activePlugin.value)
    const body = getRequestBody(activePlugin.value, text)
    const res = await apiPost(endpoint, body)
    
    const result = res.result || res.data?.result || res.answer || '抱歉，未获得有效回复'
    messages.value.push({ role: 'assistant', content: result })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `[错误] ${e.message || '请求失败，请检查网络连接'}` })
  } finally {
    loading.value = false
    await nextTick()
    scrollBottom()
  }
}

function getEndpoint(pluginId) {
  const map = {
    topics: '/api/research/generate',
    evaluate: '/api/research/evaluate',
    outline: '/api/academic/outline',
    review: '/api/academic/review',
    translate: '/api/academic/translate',
    polish: '/api/academic/polish',
  }
  return map[pluginId] || '/api/chat/blocking'
}

function getRequestBody(pluginId, text) {
  const map = {
    topics: { input: text },
    evaluate: { title: text },
    outline: { topic: text },
    review: { topic: text },
    translate: { text, target_lang: 'zh' },
    polish: { text },
  }
  return map[pluginId] || { query: text }
}

// ====== 重新生成 ======
function regenerate(msg) {
  const idx = messages.value.indexOf(msg)
  if (idx > 0) {
    const userMsg = messages.value[idx - 1]
    inputText.value = userMsg.content
    messages.value = messages.value.slice(0, idx - 1)
    sendMessage()
  }
}

// ====== 文件上传 ======
async function handleUpload(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  messages.value.push({ role: 'user', content: `📎 上传文件: ${file.name}`, title: '文件上传' })
  loading.value = true
  
  try {
    const data = await apiUpload('/api/files/upload', formData)
    messages.value.push({ role: 'assistant', content: `文件已上传并解析：\n\n${data.result || data.summary || '文件处理完成'}` })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `[文件上传失败: ${e.message}]` })
  } finally {
    loading.value = false
  }
  return false
}

// ====== 工具 ======
function clearChat() {
  messages.value = []
  activePlugin.value = null
}
function copyText(text) {
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制'))
}
function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text
  }
}
function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}
</script>

<style scoped>
.academic-workspace { min-height: calc(100vh - 100px); }

/* ====== Workspace Container ====== */
.workspace-container {
  display: flex; gap: 0; height: calc(100vh - 180px);
  margin: 12px 16px 0;
  background: #fff; border-radius: 12px; border: 1px solid var(--border-color, #e5e7eb);
  overflow: hidden;
}

/* ====== LEFT: Plugin Panel ====== */
.plugin-panel {
  width: 200px; min-width: 200px; 
  background: #f8f9fb; border-right: 1px solid var(--border-color, #e5e7eb);
  padding: 16px 12px; overflow-y: auto;
}
.panel-title {
  font-size: 12px; color: #94a3b8; font-weight: 600; text-transform: uppercase;
  letter-spacing: 1px; margin-bottom: 12px; padding: 0 4px;
}
.plugin-group { margin-bottom: 16px; }
.group-label {
  font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600;
  padding: 0 4px; margin-bottom: 6px; letter-spacing: 0.5px;
}
.plugin-btn {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  border-radius: 8px; cursor: pointer; font-size: 13px; color: #374151;
  transition: all .15s; margin-bottom: 2px;
}
.plugin-btn:hover { background: #e8ecf1; }
.plugin-btn.active { background: #1677ff12; color: #1677ff; font-weight: 600; }

.panel-divider { height: 1px; background: #e5e7eb; margin: 16px 0; }

.model-selector { margin-bottom: 14px; }
.model-label {
  font-size: 12px; color: #94a3b8; font-weight: 600; display: block; margin-bottom: 4px;
}
.param-row {
  font-size: 12px; color: #6b7280; margin-top: 4px;
}
.param-row :deep(.el-slider__input) { width: 50px; }

/* ====== RIGHT: Chat Area ====== */
.chat-area {
  flex: 1; display: flex; flex-direction: column; min-width: 0;
}

/* Messages */
.chat-messages {
  flex: 1; overflow-y: auto; padding: 20px 24px;
}
.chat-messages::-webkit-scrollbar { width: 6px; }
.chat-messages::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 3px; }

.welcome-area {
  text-align: center; padding: 60px 20px;
}
.welcome-icon { color: #1677ff; margin-bottom: 16px; opacity: 0.6; }
.welcome-area h3 { font-size: 20px; color: #1f2937; margin: 0 0 8px; }
.welcome-area p { color: #94a3b8; font-size: 14px; margin: 0 0 20px; }
.quick-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }

.msg-item { display: flex; gap: 12px; margin-bottom: 20px; }
.msg-item.user { flex-direction: row-reverse; }
.msg-avatar {
  width: 32px; height: 32px; border-radius: 8px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0;
}
.msg-item.user .msg-avatar { background: #1677ff12; color: #1677ff; }
.msg-item.assistant .msg-avatar { background: #10b98112; color: #10b981; }

.msg-content { max-width: 75%; }
.msg-item.user .msg-content { text-align: right; }
.msg-text {
  background: #f8f9fb; border-radius: 12px; padding: 12px 16px;
  font-size: 14px; line-height: 1.7; color: #1f2937;
}
.msg-item.user .msg-text { background: #1677ff; color: #fff; }
.msg-text :deep(h1), .msg-text :deep(h2), .msg-text :deep(h3) { margin: 8px 0 4px; font-size: 16px; color: inherit; }
.msg-text :deep(p) { margin: 4px 0; }
.msg-text :deep(ul), .msg-text :deep(ol) { margin: 4px 0; padding-left: 18px; }
.msg-text :deep(code) { background: #e5e7eb44; padding: 1px 4px; border-radius: 3px; font-size: 13px; }
.msg-text :deep(pre) { background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 12px; margin: 8px 0; }
.msg-text :deep(blockquote) { border-left: 3px solid #1677ff; margin: 4px 0; padding: 4px 12px; color: #6b7280; }

.msg-ops { margin-top: 6px; display: flex; gap: 4px; opacity: 0.5; }
.msg-ops:hover { opacity: 1; }

.thinking-dots { display: flex; gap: 6px; padding: 12px 16px; }
.thinking-dots span {
  width: 8px; height: 8px; border-radius: 50%; background: #94a3b8;
  animation: thinking 1.4s infinite ease-in-out both;
}
.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes thinking {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* ====== Input Area ====== */
.input-area { border-top: 1px solid var(--border-color, #e5e7eb); padding: 12px 20px 16px; }
.plugin-hint { margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.hint-text { font-size: 12px; color: #94a3b8; }

.input-row :deep(.el-textarea__inner) {
  border-radius: 10px; font-size: 14px; line-height: 1.6;
  background: #f8f9fb; border-color: #e5e7eb;
}
.input-row :deep(.el-textarea__inner:focus) { border-color: #1677ff; }

.action-bar {
  display: flex; justify-content: space-between; align-items: center; margin-top: 10px;
}
.left-actions, .right-actions { display: flex; align-items: center; gap: 8px; }

/* ====== Responsive ====== */
@media (max-width: 768px) {
  .plugin-panel { display: none; }
  .workspace-container { margin: 0; border-radius: 0; height: calc(100vh - 160px); }
  .msg-content { max-width: 90%; }
}
</style>
