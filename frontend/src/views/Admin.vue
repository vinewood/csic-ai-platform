<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&q=80);">
      <div class="hero-content">
        <h2>系统管理</h2>
        <p>用户 · 模型 · 用量 · RSS · 邮箱 · API</p>
      </div>
    </div>

    <el-card shadow="never" class="content-card">
      <el-tabs v-model="tab" class="admin-tabs">

        <!-- 用户管理 -->
        <el-tab-pane label="用户管理" name="users">
          <div class="section-toolbar">
            <el-button type="primary" size="default" :icon="Plus" @click="openUserDialog()">添加用户</el-button>
          </div>
          <el-table :data="users" stripe>
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.is_active?'success':'info'">{{ row.is_active?'活跃':'禁用' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openUserDialog(row)">编辑</el-button>
                <el-popconfirm title="确定删除此用户？" @confirm="deleteUser(row)">
                  <template #reference><el-button link type="danger" size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 模型管理 -->
        <el-tab-pane label="模型管理" name="models">
          <div class="section-toolbar">
            <el-button type="primary" size="default" :icon="Plus" @click="openModelDialog()">添加模型</el-button>
          </div>
          <el-table :data="apiModels" stripe>
            <el-table-column prop="name" label="模型标识" min-width="140" />
            <el-table-column prop="provider" label="供应商" width="110" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.status==='active'?'success':'danger'">{{ row.status==='active'?'已配置':'未配置' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openModelDialog(row)">配置</el-button>
                <el-popconfirm title="确定删除此模型？" @confirm="deleteModel(row)">
                  <template #reference><el-button link type="danger" size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 用量统计 -->
        <el-tab-pane label="用量统计" name="usage">
          <el-row :gutter="16">
            <el-col :span="6" :xs="12" v-for="s in stats" :key="s.label">
              <el-card shadow="never" class="csic-stat-card" style="cursor:pointer;" @click="openUsageDetail(s)">
                <div class="stat-value">{{ s.value }}</div>
                <div class="stat-label">{{ s.label }}</div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- RSS新闻源 -->
        <el-tab-pane label="RSS新闻源" name="rss">
          <div class="section-toolbar">
            <el-button type="primary" size="default" :icon="Plus" @click="openRssDialog()">添加源</el-button>
          </div>
          <el-table :data="rssList" stripe>
            <el-table-column prop="name" label="名称" min-width="130" />
            <el-table-column prop="url" label="URL" min-width="260" />
            <el-table-column prop="category" label="分类" width="90">
              <template #default="{ row }"><el-tag size="small" effect="light">{{ row.category }}</el-tag></template>
            </el-table-column>
            <el-table-column label="AI增强" width="100" align="center">
              <template #default="{ row }"><el-switch v-model="row.ai_enabled" size="default" /></template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }"><el-tag size="small" :type="row.active?'success':'info'">{{ row.active?'活跃':'停用' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openRssDialog(row)">编辑</el-button>
                <el-popconfirm title="确定删除此新闻源？" @confirm="deleteRss(row)">
                  <template #reference><el-button link type="danger" size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 邮箱配置 -->
        <el-tab-pane label="邮箱配置" name="email">
          <el-card shadow="never" style="max-width:600px;border:none;padding:0;">
            <el-form :model="emailConfig" label-width="120px">
              <el-form-item label="SMTP服务器"><el-input v-model="emailConfig.smtpHost" placeholder="smtp.example.com" /></el-form-item>
              <el-form-item label="端口"><el-input-number v-model="emailConfig.smtpPort" :min="1" :max="65535" style="width:120px;" /></el-form-item>
              <el-form-item label="账号"><el-input v-model="emailConfig.smtpUser" placeholder="xxx@example.com" /></el-form-item>
              <el-form-item label="密码/授权码"><el-input v-model="emailConfig.smtpPass" type="password" show-password /></el-form-item>
              <el-form-item label="发件人"><el-input v-model="emailConfig.fromAddr" placeholder="发件地址" /></el-form-item>
              <el-form-item label="收件人"><el-input v-model="emailConfig.toAddr" placeholder="接收资讯的邮箱" /></el-form-item>
              <el-form-item label="发送时间"><el-input v-model="emailConfig.sendTime" placeholder="08:00" style="width:160px;" /></el-form-item>
              <el-form-item label="自动发送"><el-switch v-model="emailConfig.autoSend" /></el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveEmailConfig">保存配置</el-button>
                <el-button @click="testEmail">测试发送</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>

        <!-- API 配置 -->
        <el-tab-pane label="API配置" name="api">
          <el-card shadow="never" style="border:none;padding:0;">
            <div class="api-split">
              <div class="api-sidebar">
                <div v-for="svc in apiServices" :key="svc.key"
                  :class="['api-svc-item', { active: selectedApi === svc.key }]"
                  @click="selectedApi = svc.key">
                  <div class="api-svc-name">{{ svc.label }}</div>
                  <div class="api-svc-desc">{{ svc.desc }}</div>
                </div>
              </div>
              <div class="api-main">
                <el-form label-width="140px" size="small">
                  <template v-if="selectedApi === 'dashscope'">
                    <h4 class="api-form-title">阿里云百炼 (DashScope)</h4>
                    <el-alert title="主要模型提供商，用于通义千问系列" type="info" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.dashscope.key" type="password" show-password placeholder="sk-xxx" /></el-form-item>
                    <el-form-item label="Endpoint"><el-input v-model="apiConfig.dashscope.endpoint" placeholder="https://dashscope.aliyuncs.com/api/v1" /></el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'deepseek'">
                    <h4 class="api-form-title">DeepSeek</h4>
                    <el-alert title="高性价比主力模型" type="success" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.deepseek.key" type="password" show-password placeholder="sk-xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.deepseek.baseUrl" placeholder="https://api.deepseek.com" /></el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'zhipu'">
                    <h4 class="api-form-title">智谱AI (GLM)</h4>
                    <el-form-item label="API Key"><el-input v-model="apiConfig.zhipu.key" type="password" show-password placeholder="xxx.xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.zhipu.baseUrl" placeholder="https://open.bigmodel.cn/api/paas/v4" /></el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'moonshot'">
                    <h4 class="api-form-title">Kimi (Moonshot)</h4>
                    <el-form-item label="API Key"><el-input v-model="apiConfig.moonshot.key" type="password" show-password placeholder="sk-xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.moonshot.baseUrl" placeholder="https://api.moonshot.cn/v1" /></el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'minimax'">
                    <h4 class="api-form-title">MiniMax</h4>
                    <el-form-item label="Group ID"><el-input v-model="apiConfig.minimax.groupId" /></el-form-item>
                    <el-form-item label="API Key"><el-input v-model="apiConfig.minimax.key" type="password" show-password /></el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'doubao'">
                    <h4 class="api-form-title">豆包 (火山引擎)</h4>
                    <el-form-item label="API Key"><el-input v-model="apiConfig.doubao.key" type="password" show-password /></el-form-item>
                    <el-form-item label="Endpoint"><el-input v-model="apiConfig.doubao.endpoint" placeholder="https://ark.cn-beijing.volces.com/api/v3" /></el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'aminer'">
                    <h4 class="api-form-title">AMiner 学术搜索</h4>
                    <el-alert title="学者/论文/机构/专利检索" type="warning" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.aminer.key" type="password" show-password placeholder="JWT Token" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.aminer.baseUrl" placeholder="https://datacenter.aminer.cn/gateway/open_platform/api" /></el-form-item>
                    <el-form-item>
                      <el-button size="small" @click="testAminerApi" :loading="testing.aminer">测试连接</el-button>
                      <span v-if="testResult.aminer !== null" :style="{color:testResult.aminer?'#10b981':'#ef4444',marginLeft:'10px',fontSize:'12px'}">
                        {{ testResult.aminer ? '已连接' : '连接失败' }}
                      </span>
                    </el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'vip'">
                    <h4 class="api-form-title">维普开放平台</h4>
                    <el-alert title="需企业签约" type="warning" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.vip.key" type="password" show-password /></el-form-item>
                    <el-form-item label="API端点"><el-input v-model="apiConfig.vip.endpoint" placeholder="https://openapi.cqvip.com" /></el-form-item>
                    <el-form-item>
                      <el-button size="small" @click="testVipApi" :loading="testing.vip">测试连接</el-button>
                      <span v-if="testResult.vip !== null" :style="{color:testResult.vip?'#10b981':'#ef4444',marginLeft:'10px',fontSize:'12px'}">
                        {{ testResult.vip ? '已连接' : '连接失败' }}
                      </span>
                    </el-form-item>
                  </template>
                  <template v-else-if="selectedApi === 'asr'">
                    <h4 class="api-form-title">音视频转录 (ASR)</h4>
                    <el-form-item label="模式">
                      <el-radio-group v-model="apiConfig.asr.mode">
                        <el-radio value="aliyun">阿里云语音识别</el-radio>
                        <el-radio value="whisper">自建 Whisper</el-radio>
                      </el-radio-group>
                    </el-form-item>
                    <template v-if="apiConfig.asr.mode === 'aliyun'">
                      <el-form-item label="Access Key ID"><el-input v-model="apiConfig.asr.aliyunKey" type="password" show-password /></el-form-item>
                      <el-form-item label="Access Key Secret"><el-input v-model="apiConfig.asr.aliyunSecret" type="password" show-password /></el-form-item>
                    </template>
                    <template v-else>
                      <el-form-item label="Whisper地址"><el-input v-model="apiConfig.asr.whisperUrl" /></el-form-item>
                      <el-form-item label="模型大小">
                        <el-select v-model="apiConfig.asr.whisperModel" style="width:100%;">
                          <el-option label="tiny" value="tiny" /><el-option label="base" value="base" />
                          <el-option label="small" value="small" /><el-option label="medium" value="medium" />
                        </el-select>
                      </el-form-item>
                    </template>
                  </template>
                  <el-divider />
                  <el-button type="primary" @click="saveApiConfig" :loading="savingApi">保存配置</el-button>
                </el-form>
              </div>
            </div>
          </el-card>
        </el-tab-pane>

        <!-- Dify 集成 -->
        <el-tab-pane label="Dify集成" name="dify">
          <el-card shadow="never" style="margin-bottom:12px">
            <template #header><span style="font-weight:700">开源项目集成状态</span></template>
            <el-row :gutter="16">
              <el-col :span="8" v-for="item in integrations" :key="item.id">
                <el-card shadow="hover" style="margin-bottom:12px">
                  <div style="display:flex;align-items:center;justify-content:space-between">
                    <strong>{{ item.name }}</strong>
                    <el-tag :type="item.status==='online'?'success':'danger'" size="small">{{ item.status==='online'?'运行中':'离线' }}</el-tag>
                  </div>
                  <p style="color:#999;font-size:12px;margin-top:8px">{{ item.desc }}</p>
                  <el-button size="small" v-if="item.url" style="margin-top:6px" @click="window.open(item.url)">打开</el-button>
                </el-card>
              </el-col>
            </el-row>
          </el-card>

          <el-card shadow="never">
            <template #header><span style="font-weight:700">Dify 知识引擎管理</span></template>
            <el-row :gutter="12">
              <el-col :xs="12" :sm="6" v-for="card in difyCards" :key="card.key">
                <el-card shadow="hover" class="dify-card" @click="card.action()">
                  <div style="font-size:32px;text-align:center;margin-bottom:8px">{{ card.icon }}</div>
                  <div style="text-align:center;font-weight:600;font-size:14px">{{ card.title }}</div>
                  <div style="text-align:center;color:#94a3b8;font-size:11px;margin-top:4px">{{ card.desc }}</div>
                </el-card>
              </el-col>
            </el-row>

            <el-divider />
            <div style="font-weight:700;margin-bottom:8px">Dify 账号信息</div>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="管理员邮箱">admin@csic.cn</el-descriptions-item>
              <el-descriptions-item label="管理员密码">***REMOVED-PASSWORD***</el-descriptions-item>
              <el-descriptions-item label="初始数据集">6个（党建/船舶/教学/政策/测试/CSIC政策）</el-descriptions-item>
              <el-descriptions-item label="集成方式">后端API代理 + DB直查</el-descriptions-item>
            </el-descriptions>

            <el-divider />
            <div style="font-weight:700;margin-bottom:8px">扩展开源工具</div>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="dify_tools (Go)">{{ difyToolsStatus }}</el-descriptions-item>
              <el-descriptions-item label="能力">PPT/Word生成 · 动态知识库 · DB查询</el-descriptions-item>
              <el-descriptions-item label="gpt_academic">/opt/gpt_academic — 科研辅助引擎</el-descriptions-item>
              <el-descriptions-item label="RSSHub">Docker部署 — 新闻聚合</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-tab-pane>

      </el-tabs>
    </el-card>

    <!-- 用户对话框 -->
    <el-dialog v-model="userDialog.visible" :title="userDialog.isEdit?'编辑用户':'添加用户'" width="450px" destroy-on-close>
      <el-form :model="userDialog.form" label-width="70px">
        <el-form-item label="用户名"><el-input v-model="userDialog.form.name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="userDialog.form.email" /></el-form-item>
        <el-form-item v-if="!userDialog.isEdit" label="密码"><el-input v-model="userDialog.form.password" placeholder="默认 ***REMOVED-PASSWORD***" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialog.visible=false">取消</el-button>
        <el-button type="primary" @click="confirmUser">确认</el-button>
      </template>
    </el-dialog>

    <!-- 模型对话框 -->
    <el-dialog v-model="modelDialog.visible" :title="modelDialog.isEdit?'配置模型':'添加模型'" width="450px" destroy-on-close>
      <el-form :model="modelDialog.form" label-width="90px">
        <el-form-item label="模型名称"><el-input v-model="modelDialog.form.name" placeholder="如 deepseek-chat" /></el-form-item>
        <el-form-item label="API Key"><el-input v-model="modelDialog.form.key" type="password" show-password /></el-form-item>
        <el-form-item label="Base URL"><el-input v-model="modelDialog.form.baseUrl" placeholder="如 https://api.deepseek.com" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialog.visible=false">取消</el-button>
        <el-button type="primary" @click="confirmModel">确认</el-button>
      </template>
    </el-dialog>

    <!-- RSS对话框 -->
    <el-dialog v-model="rssDialog.visible" :title="rssDialog.isEdit?'编辑新闻源':'添加新闻源'" width="450px" destroy-on-close>
      <el-form :model="rssDialog.form" label-width="70px">
        <el-form-item label="名称"><el-input v-model="rssDialog.form.name" /></el-form-item>
        <el-form-item label="RSS URL"><el-input v-model="rssDialog.form.url" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="rssDialog.form.category" style="width:100%;">
            <el-option label="官方" value="官方" /><el-option label="党建" value="党建" /><el-option label="科研" value="科研" />
            <el-option label="制造业" value="制造业" /><el-option label="科技" value="科技" /><el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="AI增强"><el-switch v-model="rssDialog.form.ai_enabled" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rssDialog.visible=false">取消</el-button>
        <el-button type="primary" @click="confirmRss">确认</el-button>
      </template>
    </el-dialog>

    <!-- 用量详情 -->
    <el-dialog v-model="usageVisible" :title="'用量详情 — ' + usageLabel" width="600px" destroy-on-close>
      <el-table :data="usageData" stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="value" label="数值" />
        <el-table-column prop="note" label="备注" min-width="200" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPost, apiPut, apiDelete } from '../api.js'

const tab = ref('users')
const API = window.location.port === '5173' ? 'http://localhost:8000' : ''

// ========== 用户管理 ==========
const userDialog = reactive({ visible: false, isEdit: false, form: { name: '', email: '', password: '' } })
const users = ref([])

function openUserDialog(row) {
  if (row) {
    userDialog.isEdit = true
    userDialog.form = { id: row.id, name: row.username, email: row.email, password: '' }
  } else {
    userDialog.isEdit = false
    userDialog.form = { name: '', email: '', password: '' }
  }
  userDialog.visible = true
}

async function confirmUser() {
  try {
    if (userDialog.isEdit) {
      await apiPut(`/api/users/${userDialog.form.id}`, { name: userDialog.form.name, email: userDialog.form.email })
    } else {
      await apiPost('/api/users', { username: userDialog.form.name, email: userDialog.form.email, password: userDialog.form.password || '***REMOVED-PASSWORD***' })
    }
    userDialog.visible = false
    ElMessage.success('已保存')
    await loadUsers()
  } catch (e) { ElMessage.error('保存失败: ' + (e.message || '未知错误')) }
}

async function deleteUser(row) {
  await apiDelete(`/api/users/${row.id}`)
  ElMessage.success('已删除')
  await loadUsers()
}

async function loadUsers() {
  const res = await apiGet('/api/users')
  users.value = Array.isArray(res) ? res : []
}

// ========== 模型管理 ==========
const modelDialog = reactive({ visible: false, isEdit: false, form: { id: null, name: '', key: '', baseUrl: '' } })
const apiModels = ref([])

function openModelDialog(row) {
  if (row) {
    modelDialog.isEdit = true
    modelDialog.form = { id: row.id, name: row.name, key: row.key || '', baseUrl: row.baseUrl || '' }
  } else {
    modelDialog.isEdit = false
    modelDialog.form = { id: null, name: '', key: '', baseUrl: '' }
  }
  modelDialog.visible = true
}

async function confirmModel() {
  const body = { name: modelDialog.form.name, key: modelDialog.form.key, base_url: modelDialog.form.baseUrl }
  if (modelDialog.isEdit) {
    await apiPut(`/api/models/${modelDialog.form.id}`, body)
  } else {
    await apiPost('/api/models', body)
  }
  modelDialog.visible = false
  ElMessage.success('已保存')
  await loadModels()
}

async function deleteModel(row) {
  await apiDelete(`/api/models/${row.id}`)
  ElMessage.success('已删除')
  await loadModels()
}

async function loadModels() {
  const res = await apiGet('/api/models')
  apiModels.value = Array.isArray(res) ? res : []
}

// ========== 用量统计 → 真实数据库查询 ==========
const stats = ref([
  { label: '本月对话', value: '--', key: 'month_conv' },
  { label: 'Token用量', value: '--', key: 'tokens' },
  { label: '活跃用户', value: '--', key: 'users' },
  { label: '日均对话', value: '--', key: 'daily' },
])
const usageVisible = ref(false)
const usageLabel = ref('')
const usageData = ref([])

async function loadUsage() {
  const res = await apiGet('/api/usage/stats')
  if (!res) return
  if (res.stats) {
    res.stats.forEach(s => {
      const found = stats.value.find(ss => ss.key === s.key)
      if (found) found.value = s.value
    })
  }
}

async function openUsageDetail(s) {
  usageLabel.value = s.label
  const res = await apiGet('/api/usage/daily')
  if (res && res.daily) {
    usageData.value = res.daily.map(d => ({
      date: d.date,
      value: s.key === 'tokens' ? (d.tokens >= 1000 ? (d.tokens / 1000).toFixed(1) + 'K' : d.tokens) : d.messages,
      note: s.key === 'tokens' ? '估算值' : '消息数'
    }))
  }
  usageVisible.value = true
}

// ========== RSS新闻源 ==========
const rssDialog = reactive({ visible: false, isEdit: false, form: { id: null, name: '', url: '', category: '其他', ai_enabled: true } })
const rssList = ref([])

function openRssDialog(row) {
  if (row) {
    rssDialog.isEdit = true
    rssDialog.form = { id: row.id, name: row.name || '', url: row.url || '', category: row.category || '其他', ai_enabled: row.ai_enabled ?? true }
  } else {
    rssDialog.isEdit = false
    rssDialog.form = { id: null, name: '', url: '', category: '其他', ai_enabled: true }
  }
  rssDialog.visible = true
}

async function confirmRss() {
  const body = { name: rssDialog.form.name, url: rssDialog.form.url, category: rssDialog.form.category, ai_enabled: rssDialog.form.ai_enabled }
  if (rssDialog.isEdit) {
    await apiPut(`/api/rss/sources/${rssDialog.form.id}`, body)
  } else {
    await apiPost('/api/rss/sources', body)
  }
  rssDialog.visible = false
  ElMessage.success('已保存')
  await loadRss()
}

async function deleteRss(row) {
  await apiDelete(`/api/rss/sources/${row.id}`)
  ElMessage.success('已删除')
  await loadRss()
}

async function loadRss() {
  const res = await apiGet('/api/rss/sources')
  rssList.value = Array.isArray(res) ? res : []
}

// ========== 邮箱配置 ==========
const emailConfig = reactive({
  smtpHost: '', smtpPort: 465, smtpUser: '', smtpPass: '',
  fromAddr: '', toAddr: '', sendTime: '08:00', autoSend: false
})

async function loadEmailConfig() {
  const res = await apiGet('/api/email/config')
  if (res) {
    emailConfig.smtpHost = res.smtp_host || ''
    emailConfig.smtpPort = res.smtp_port || 465
    emailConfig.smtpUser = res.smtp_user || ''
    emailConfig.smtpPass = ''
    emailConfig.fromAddr = res.from_addr || ''
    emailConfig.toAddr = res.to_addr || ''
    emailConfig.sendTime = res.send_time || '08:00'
    emailConfig.autoSend = res.auto_send || false
  }
}

async function saveEmailConfig() {
  await apiPut('/api/email/config', {
    smtp_host: emailConfig.smtpHost, smtp_port: emailConfig.smtpPort,
    smtp_user: emailConfig.smtpUser, smtp_pass: emailConfig.smtpPass,
    from_addr: emailConfig.fromAddr, to_addr: emailConfig.toAddr,
    send_time: emailConfig.sendTime || '08:00', auto_send: emailConfig.autoSend,
  })
  ElMessage.success('邮箱配置已保存')
}

async function testEmail() {
  await apiPost('/api/email/test', {})
  ElMessage.success('测试邮件发送成功')
}

// ========== API 配置 — 逐个 Provider 保存到数据库 ==========
const selectedApi = ref('deepseek')
const savingApi = ref(false)
const apiServices = [
  { key: 'dashscope', label: '阿里云百炼', desc: '通义千问主力模型' },
  { key: 'deepseek', label: 'DeepSeek', desc: '高性价比模型' },
  { key: 'zhipu', label: '智谱AI (GLM)', desc: '长文本处理' },
  { key: 'moonshot', label: 'Kimi (Moonshot)', desc: '超长上下文' },
  { key: 'minimax', label: 'MiniMax', desc: '创意写作' },
  { key: 'doubao', label: '豆包 (火山引擎)', desc: '低延迟部署' },
  { key: 'aminer', label: 'AMiner 学术', desc: '学者/论文检索' },
  { key: 'vip', label: '维普开放平台', desc: '文献/引文分析' },
  { key: 'asr', label: '音视频转录', desc: 'ASR 语音识别' },
]

const defaultConfig = () => ({
  dashscope: { key: '', endpoint: 'https://dashscope.aliyuncs.com/api/v1' },
  deepseek: { key: '', baseUrl: 'https://api.deepseek.com' },
  zhipu: { key: '', baseUrl: 'https://open.bigmodel.cn/api/paas/v4' },
  moonshot: { key: '', baseUrl: 'https://api.moonshot.cn/v1' },
  minimax: { groupId: '', key: '' },
  doubao: { key: '', endpoint: 'https://ark.cn-beijing.volces.com/api/v3' },
  aminer: { key: '', baseUrl: 'https://datacenter.aminer.cn/gateway/open_platform/api' },
  vip: { key: '', endpoint: 'https://openapi.cqvip.com' },
  asr: { mode: 'aliyun', aliyunKey: '', aliyunSecret: '', whisperUrl: 'http://localhost:9000', whisperModel: 'medium' },
})
const apiConfig = reactive(defaultConfig())

// 前端 key → 后端 provider 映射
const frontToBack = {
  dashscope: 'qwen', deepseek: 'deepseek', zhipu: 'zhipu',
  moonshot: 'kimi', minimax: 'minimax', doubao: 'doubao',
  aminer: 'aminer', vip: 'vip', asr: 'asr',
}

async function loadApiConfigs() {
  for (const [fk, bk] of Object.entries(frontToBack)) {
    try {
      const res = await apiGet(`/api/config/${bk}`)
      if (res && res.key) {
        apiConfig[fk] = { ...apiConfig[fk], ...res }
      }
    } catch (e) { /* no config yet */ }
  }
}

async function saveApiConfig() {
  savingApi.value = true
  const fk = selectedApi.value
  const bk = frontToBack[fk]
  const cfg = { ...apiConfig[fk] } // snapshot reactive object

  if (!bk) { ElMessage.warning('未知服务'); savingApi.value = false; return }
  try {
    await apiPut(`/api/config/${bk}`, { config_json: cfg })
    ElMessage.success(`${apiServices.find(s => s.key === fk)?.label || fk} 配置已保存到数据库`)
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  }
  savingApi.value = false
}

// ========== API 测试 ==========
const testing = reactive({ aminer: false, vip: false })
const testResult = reactive({ aminer: null, vip: null })

async function testAminerApi() {
  if (!apiConfig.aminer.key) { ElMessage.warning('请先填写 API Key'); return }
  testing.aminer = true; testResult.aminer = null
  try {
    const resp = await fetch(apiConfig.aminer.baseUrl + '/paper/search/pro?page=0&size=1', {
      headers: { 'Authorization': 'Bearer ' + apiConfig.aminer.key }
    })
    testResult.aminer = resp.ok
    ElMessage[resp.ok ? 'success' : 'error'](resp.ok ? 'AMiner API 连接成功' : '连接失败: ' + resp.status)
  } catch (e) { testResult.aminer = false; ElMessage.error('连接异常') }
  finally { testing.aminer = false }
}

async function testVipApi() {
  if (!apiConfig.vip.key) { ElMessage.warning('请先填写 API Key'); return }
  testing.vip = true; testResult.vip = null
  try {
    const resp = await fetch(apiConfig.vip.endpoint + '/api/v3/search', {
      signal: AbortSignal.timeout(8000)
    })
    testResult.vip = resp.ok
    ElMessage[resp.ok ? 'success' : 'error'](resp.ok ? '维普 API 连接成功' : '连接失败')
  } catch (e) { testResult.vip = false; ElMessage.error('连接异常') }
  finally { testing.vip = false }
}

// ========== Dify 集成 ==========
const integrations = ref([])
const difyHealth = ref(null)
const difyToolsStatus = ref('检查中...')
const difyUrl = ref('https://csic.thinkalike.com.cn/dify/')

const difyCards = [
  { key:'console', icon:'🔧', title:'Dify 控制台', desc:'管理知识库/应用/工作流', action:()=>window.open('/dify/') },
  { key:'init', icon:'🔄', title:'重新初始化', desc:'重置Dify管理员账号', action:initDify },
  { key:'kb', icon:'📚', title:'知识库管理', desc:'数据集/文档/检索', action:()=>window.open('/#/workspace/knowledge','_self') },
  { key:'health', icon:'🏥', title:'健康检查', desc:'检查服务状态', action:testDifyStatusFn },
]

async function fetchIntegrations() {
  const res = await apiGet('/api/admin/integrations')
  if (res && res.integrations) integrations.value = res.integrations
}

async function initDify() {
  try { await apiPost('/api/dify/init', {}); ElMessage.success('Dify已重新初始化') }
  catch { ElMessage.warning('请手动访问Dify控制台完成初始化: admin@csic.cn / ***REMOVED-PASSWORD***') }
}

async function testDifyStatusFn() {
  const res = await apiGet('/api/dify/health')
  difyHealth.value = res || {}
  ElMessage.success('检查完成: ' + (res?.status || '未响应'))
}

async function openDifyConsole() { window.open(difyUrl.value) }
function goToKnowledge() { window.open('/#/workspace/knowledge', '_self') }

// ========== 初始化 ==========
onMounted(async () => {
  await Promise.allSettled([
    loadUsers(), loadModels(), loadRss(), loadEmailConfig(),
    loadApiConfigs(), loadUsage(), fetchIntegrations(),
  ])
  testDifyStatusFn()
})

async function testDifyStatus() { testDifyStatusFn() }
</script>

<style scoped>
.content-card { border-radius: 8px; border: 1px solid var(--border-color); }
.section-toolbar { margin-bottom: 14px; display: flex; justify-content: flex-end; }
.admin-tabs :deep(.el-tabs__item) { font-size: 14px; }
.api-split { display: flex; gap: 16px; min-height: 420px; }
.api-split .api-sidebar { width: 200px; flex-shrink: 0; border-right: 1px solid var(--border-color); padding-right: 12px; }
.api-split .api-svc-item { padding: 10px 12px; cursor: pointer; border-radius: 6px; transition: all .15s; margin-bottom: 2px; }
.api-split .api-svc-item:hover { background: #f6f8fa; }
.api-split .api-svc-item.active { background: #f0f5ff; border: 1px solid #bae0ff; }
.api-split .api-svc-name { font-weight: 600; font-size: 13px; color: var(--text-main); }
.api-split .api-svc-desc { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.api-split .api-main { flex: 1; min-width: 0; padding-left: 4px; }
.api-form-title { margin: 0 0 12px; font-size: 16px; font-weight: 700; color: var(--text-main); }
.dify-card { cursor:pointer; border-radius:10px; border:1px solid #e5e7eb; transition:all .15s; padding:16px 8px; }
.dify-card:hover { border-color:#1677ff; box-shadow:0 4px 12px rgba(22,119,255,.1); transform:translateY(-2px); }
</style>
