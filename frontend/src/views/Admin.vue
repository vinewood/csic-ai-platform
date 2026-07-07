<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&q=80);">
      <div class="hero-content">
        <h2>系统管理</h2>
        <p>用户 · 模型 · 用量 · RSS · 邮箱</p>
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
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.status==='active'?'success':'info'">{{ row.status==='active'?'活跃':'禁用' }}</el-tag></template>
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
            <el-table-column prop="name" label="模型名称" min-width="180" />
            <el-table-column prop="provider" label="供应商" width="130" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.status==='active'?'success':'danger'">{{ row.status==='active'?'启用':'停用' }}</el-tag></template>
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
              <template #default="{ row }">
                <el-switch v-model="row.aiEnabled" size="default" />
              </template>
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
              <el-form-item label="发送时间">
                <el-time-picker v-model="emailConfig.sendTime" format="HH:mm" placeholder="选择时间" style="width:160px;" />
              </el-form-item>
              <el-form-item label="自动发送">
                <el-switch v-model="emailConfig.autoSend" />
                <span style="margin-left:10px;font-size:12px;color:#94a3b8;">每天定时发送整理好的资讯</span>
              </el-form-item>
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
              <!-- 左侧：服务列表 -->
              <div class="api-sidebar">
                <div
                  v-for="svc in apiServices"
                  :key="svc.key"
                  :class="['api-svc-item', { active: selectedApi === svc.key }]"
                  @click="selectedApi = svc.key"
                >
                  <div class="api-svc-name">{{ svc.label }}</div>
                  <div class="api-svc-desc">{{ svc.desc }}</div>
                </div>
              </div>
              <!-- 右侧：配置表单 -->
              <div class="api-main">
                <el-form label-width="140px" size="small">
                  <!-- 阿里云百炼 -->
                  <template v-if="selectedApi === 'dashscope'">
                    <h4 class="api-form-title">阿里云百炼 (DashScope)</h4>
                    <el-alert title="主要模型提供商，用于通义千问系列" type="info" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.dashscope.key" type="password" show-password placeholder="sk-xxx" /></el-form-item>
                    <el-form-item label="Endpoint"><el-input v-model="apiConfig.dashscope.endpoint" placeholder="https://dashscope.aliyuncs.com/api/v1" /></el-form-item>
                    <el-form-item label="可用模型"><el-checkbox-group v-model="apiConfig.dashscope.models">
                      <el-checkbox label="qwen-max">通义千问 Max</el-checkbox><el-checkbox label="qwen-plus">通义千问 Plus</el-checkbox><el-checkbox label="qwen-turbo">通义千问 Turbo</el-checkbox>
                    </el-checkbox-group></el-form-item>
                  </template>
                  <!-- DeepSeek -->
                  <template v-else-if="selectedApi === 'deepseek'">
                    <h4 class="api-form-title">DeepSeek</h4>
                    <el-alert title="高性价比主力模型，¥2.16/M tokens" type="success" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.deepseek.key" type="password" show-password placeholder="sk-xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.deepseek.baseUrl" placeholder="https://api.deepseek.com" /></el-form-item>
                    <el-form-item label="可用模型"><el-checkbox-group v-model="apiConfig.deepseek.models">
                      <el-checkbox label="deepseek-chat">DeepSeek Chat</el-checkbox><el-checkbox label="deepseek-v4-flash">DeepSeek V4 Flash</el-checkbox><el-checkbox label="deepseek-v4-pro">DeepSeek V4 Pro</el-checkbox>
                    </el-checkbox-group></el-form-item>
                  </template>
                  <!-- 智谱AI -->
                  <template v-else-if="selectedApi === 'zhipu'">
                    <h4 class="api-form-title">智谱AI (GLM)</h4>
                    <el-alert title="长文本处理优势，适合文献分析" type="info" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.zhipu.key" type="password" show-password placeholder="xxx.xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.zhipu.baseUrl" placeholder="https://open.bigmodel.cn/api/paas/v4" /></el-form-item>
                    <el-form-item label="可用模型"><el-checkbox-group v-model="apiConfig.zhipu.models">
                      <el-checkbox label="glm-4-plus">GLM-4-Plus</el-checkbox><el-checkbox label="glm-4">GLM-4</el-checkbox><el-checkbox label="glm-4-flash">GLM-4-Flash</el-checkbox>
                    </el-checkbox-group></el-form-item>
                  </template>
                  <!-- Kimi Moonshot -->
                  <template v-else-if="selectedApi === 'moonshot'">
                    <h4 class="api-form-title">Kimi (Moonshot)</h4>
                    <el-alert title="超长上下文（128K），适合整篇论文分析" type="info" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.moonshot.key" type="password" show-password placeholder="sk-xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.moonshot.baseUrl" placeholder="https://api.moonshot.cn/v1" /></el-form-item>
                    <el-form-item label="可用模型"><el-checkbox-group v-model="apiConfig.moonshot.models">
                      <el-checkbox label="moonshot-v1-8k">Moonshot v1 8K</el-checkbox><el-checkbox label="moonshot-v1-32k">Moonshot v1 32K</el-checkbox><el-checkbox label="moonshot-v1-128k">Moonshot v1 128K</el-checkbox>
                    </el-checkbox-group></el-form-item>
                  </template>
                  <!-- MiniMax -->
                  <template v-else-if="selectedApi === 'minimax'">
                    <h4 class="api-form-title">MiniMax</h4>
                    <el-alert title="创意写作场景优势" type="info" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="Group ID"><el-input v-model="apiConfig.minimax.groupId" placeholder="MiniMax Group ID" /></el-form-item>
                    <el-form-item label="API Key"><el-input v-model="apiConfig.minimax.key" type="password" show-password placeholder="sk-xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.minimax.baseUrl" placeholder="https://api.minimax.chat/v1" /></el-form-item>
                    <el-form-item label="可用模型"><el-checkbox-group v-model="apiConfig.minimax.models">
                      <el-checkbox label="abab6.5">abab6.5</el-checkbox><el-checkbox label="abab6.5s">abab6.5s</el-checkbox><el-checkbox label="abab5.5">abab5.5</el-checkbox>
                    </el-checkbox-group></el-form-item>
                  </template>
                  <!-- 豆包 -->
                  <template v-else-if="selectedApi === 'doubao'">
                    <h4 class="api-form-title">豆包 (火山引擎)</h4>
                    <el-alert title="部署在阿里云上延迟更低" type="info" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.doubao.key" type="password" show-password placeholder="xxx" /></el-form-item>
                    <el-form-item label="Endpoint"><el-input v-model="apiConfig.doubao.endpoint" placeholder="https://ark.cn-beijing.volces.com/api/v3" /></el-form-item>
                    <el-form-item label="可用模型"><el-checkbox-group v-model="apiConfig.doubao.models">
                      <el-checkbox label="doubao-pro">豆包 Pro</el-checkbox><el-checkbox label="doubao-lite">豆包 Lite</el-checkbox>
                    </el-checkbox-group></el-form-item>
                  </template>
                  <!-- AMiner -->
                  <template v-else-if="selectedApi === 'aminer'">
                    <h4 class="api-form-title">AMiner 学术搜索</h4>
                    <el-alert title="学者/论文/机构/专利检索，约 ¥3,660/年" type="warning" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.aminer.key" type="password" show-password placeholder="xxx" /></el-form-item>
                    <el-form-item label="Base URL"><el-input v-model="apiConfig.aminer.baseUrl" placeholder="https://api.aminer.cn" /></el-form-item>
                    <el-form-item label="服务"><el-checkbox-group v-model="apiConfig.aminer.services">
                      <el-checkbox label="scholar">学者搜索</el-checkbox><el-checkbox label="paper">论文检索</el-checkbox><el-checkbox label="institution">机构分析</el-checkbox><el-checkbox label="patent">专利查询</el-checkbox>
                    </el-checkbox-group></el-form-item>
                    <el-form-item>
                      <el-button size="small" :icon="Connection" @click="testAminerApi" :loading="testing.aminer">测试连接</el-button>
                      <span v-if="testResult.aminer !== null" :style="{color:testResult.aminer?'#10b981':'#ef4444',marginLeft:'10px',fontSize:'12px'}">
                        {{ testResult.aminer ? '✓ 连接成功' : '✗ 连接失败' }}
                      </span>
                    </el-form-item>
                  </template>
                  <!-- 维普 -->
                  <template v-else-if="selectedApi === 'vip'">
                    <h4 class="api-form-title">维普开放平台</h4>
                    <el-alert title="需企业签约，年费 ¥8,000-15,000" type="warning" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="API Key"><el-input v-model="apiConfig.vip.key" type="password" show-password placeholder="xx-xxx" /></el-form-item>
                    <el-form-item label="API端点"><el-input v-model="apiConfig.vip.endpoint" placeholder="https://openapi.cqvip.com" /></el-form-item>
                    <el-form-item label="服务"><el-checkbox-group v-model="apiConfig.vip.services">
                      <el-checkbox label="literature">文献检索</el-checkbox><el-checkbox label="citation">引文分析</el-checkbox><el-checkbox label="journal">期刊导航</el-checkbox><el-checkbox label="trend">研究趋势</el-checkbox>
                    </el-checkbox-group></el-form-item>
                    <el-form-item>
                      <el-button size="small" :icon="Connection" @click="testVipApi" :loading="testing.vip">测试连接</el-button>
                      <span v-if="testResult.vip !== null" :style="{color:testResult.vip?'#10b981':'#ef4444',marginLeft:'10px',fontSize:'12px'}">
                        {{ testResult.vip ? '✓ 连接成功' : '✗ 连接失败' }}
                      </span>
                    </el-form-item>
                  </template>
                  <!-- 音视频转录 -->
                  <template v-else-if="selectedApi === 'asr'">
                    <h4 class="api-form-title">音视频转录 (ASR)</h4>
                    <el-alert title="一期用阿里云API（¥3,500/年），二期可自建Faster-Whisper" type="info" :closable="false" show-icon style="margin-bottom:16px;" />
                    <el-form-item label="模式">
                      <el-radio-group v-model="apiConfig.asr.mode">
                        <el-radio value="aliyun">阿里云语音识别</el-radio>
                        <el-radio value="whisper">自建 Faster-Whisper</el-radio>
                      </el-radio-group>
                    </el-form-item>
                    <template v-if="apiConfig.asr.mode === 'aliyun'">
                      <el-form-item label="Access Key ID"><el-input v-model="apiConfig.asr.aliyunKey" type="password" show-password placeholder="LTAIxxx" /></el-form-item>
                      <el-form-item label="Access Key Secret"><el-input v-model="apiConfig.asr.aliyunSecret" type="password" show-password placeholder="xxx" /></el-form-item>
                      <el-form-item label="语音识别端点"><el-input v-model="apiConfig.asr.aliyunEndpoint" placeholder="https://speech.aliyuncs.com" /></el-form-item>
                    </template>
                    <template v-else>
                      <el-form-item label="Whisper 服务地址"><el-input v-model="apiConfig.asr.whisperUrl" placeholder="http://localhost:9000" /></el-form-item>
                      <el-form-item label="模型大小"><el-select v-model="apiConfig.asr.whisperModel" style="width:100%;">
                        <el-option label="tiny (约1GB)" value="tiny" /><el-option label="base (约1.4GB)" value="base" />
                        <el-option label="small (约4.6GB)" value="small" /><el-option label="medium (约12GB)" value="medium" /><el-option label="large (约25GB)" value="large" />
                      </el-select></el-form-item>
                      <el-form-item label="语言"><el-select v-model="apiConfig.asr.whisperLang" style="width:100%;">
                        <el-option label="中文" value="zh" /><el-option label="英文" value="en" /><el-option label="自动检测" value="auto" />
                      </el-select></el-form-item>
                    </template>
                  </template>
                  <el-divider />
                  <el-button type="primary" @click="saveApiConfig">保存配置</el-button>
                </el-form>
              </div>
            </div>
          </el-card>
        </el-tab-pane>

        <!-- Dify / 集成项目面板 -->
        <el-tab-pane label="Dify集成" name="dify">
          <el-card shadow="never">
            <template #header><span style="font-weight:700">开源项目集成状态</span></template>
            <el-row :gutter="16">
              <el-col :span="8" v-for="item in integrations" :key="item.id">
                <el-card shadow="hover" style="margin-bottom:12px">
                  <div style="display:flex;align-items:center;justify-content:space-between">
                    <strong>{{ item.name }}</strong>
                    <el-tag :type="item.status==='online'?'success':'danger'" size="small">{{ item.status }}</el-tag>
                  </div>
                  <p style="color:#999;font-size:12px;margin-top:8px">{{ item.desc }}</p>
                </el-card>
              </el-col>
            </el-row>

            <el-divider />

            <template #header><span style="font-weight:700">Dify 知识库同步</span></template>
            <el-select v-model="difySync.kbId" placeholder="选择本地知识库" style="width:240px;margin-right:12px" @change="fetchDifyDatasets">
              <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
            </el-select>
            <el-button type="primary" @click="syncToDify" :disabled="!difySync.kbId">同步到 Dify</el-button>
            <p style="color:#999;font-size:12px;margin-top:8px">将本地知识库文档上传到 Dify，启用 RAG 增强检索</p>
          </el-card>
        </el-tab-pane>

      </el-tabs>
    </el-card>

    <!-- 用户对话框 -->
    <el-dialog v-model="userDialog.visible" :title="userDialog.isEdit?'编辑用户':'添加用户'" width="450px" destroy-on-close>
      <el-form :model="userDialog.form" label-width="80px">
        <el-form-item label="姓名"><el-input v-model="userDialog.form.name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="userDialog.form.email" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialog.visible=false">取消</el-button>
        <el-button type="primary" @click="confirmUser">确认</el-button>
      </template>
    </el-dialog>

    <!-- 模型对话框 -->
    <el-dialog v-model="modelDialog.visible" :title="modelDialog.isEdit?'配置模型':'添加模型'" width="450px" destroy-on-close>
      <el-form :model="modelDialog.form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="modelDialog.form.name" /></el-form-item>
        <el-form-item label="API Key"><el-input v-model="modelDialog.form.key" type="password" show-password /></el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="modelDialog.form.provider" style="width:100%;">
            <el-option label="阿里云百炼" value="阿里云" />
            <el-option label="DeepSeek" value="DeepSeek" />
            <el-option label="智谱AI" value="智谱AI" />
          </el-select>
        </el-form-item>
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
            <el-option label="官方" value="官方" /><el-option label="党建" value="党建" />
            <el-option label="科研" value="科研" /><el-option label="制造业" value="制造业" />
            <el-option label="造船" value="造船" /><el-option label="经济" value="经济" />
            <el-option label="科技" value="科技" /><el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="AI增强">
          <el-switch v-model="rssDialog.form.aiEnabled" />
        </el-form-item>
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
        <el-table-column prop="value" label="数值" width="100" />
        <el-table-column prop="note" label="备注" min-width="200" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPost, apiPut, apiDelete } from '../api.js'

const tab = ref('users')

// ========== 用户管理 ==========
const userDialog = reactive({ visible: false, isEdit: false, form: { name: '', email: '' } })
const users = ref([])

function openUserDialog(row) {
  if (row) { userDialog.isEdit = true; Object.assign(userDialog.form, { name: row.name, email: row.email }) }
  else { userDialog.isEdit = false; Object.assign(userDialog.form, { name: '', email: '' }) }
  userDialog.visible = true
}

async function confirmUser() {
  try {
    if (userDialog.isEdit) {
      await apiPut(`/api/users/${userDialog.form.email}`, userDialog.form)
    } else {
      await apiPost('/api/users', userDialog.form)
    }
    userDialog.visible = false
    ElMessage.success('已保存')
    await loadUsers()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  }
}

async function deleteUser(row) {
  try {
    await apiDelete(`/api/users/${row.id || row.email}`)
    ElMessage.success('已删除')
    await loadUsers()
  } catch (e) {
    ElMessage.error('删除失败: ' + (e.message || '未知错误'))
  }
}

async function loadUsers() {
  try {
    const res = await apiGet('/api/users')
    users.value = Array.isArray(res) ? res : (res.data || res.users || [])
  } catch (e) {
    users.value = []
  }
}

// ========== 模型管理 ==========
const modelDialog = reactive({ visible: false, isEdit: false, form: { name: '', key: '', provider: '' } })
const apiModels = ref([])

function openModelDialog(row) {
  if (row) { modelDialog.isEdit = true; Object.assign(modelDialog.form, { name: row.name, key: row.key || '', provider: row.provider || '' }) }
  else { modelDialog.isEdit = false; Object.assign(modelDialog.form, { name: '', key: '', provider: '' }) }
  modelDialog.visible = true
}

async function confirmModel() {
  try {
    if (modelDialog.isEdit) {
      await apiPut(`/api/models/${modelDialog.form.name}`, modelDialog.form)
    } else {
      await apiPost('/api/models', modelDialog.form)
    }
    modelDialog.visible = false
    ElMessage.success('已保存')
    await loadModels()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  }
}

async function deleteModel(row) {
  try {
    await apiDelete(`/api/models/${row.id || row.name}`)
    ElMessage.success('已删除')
    await loadModels()
  } catch (e) {
    ElMessage.error('删除失败: ' + (e.message || '未知错误'))
  }
}

async function loadModels() {
  try {
    const res = await apiGet('/api/models')
    apiModels.value = Array.isArray(res) ? res : (res.data || res.models || [])
  } catch (e) {
    apiModels.value = []
  }
}

// ========== 用量统计 ==========
const stats = [
  { label: '本月调用', value: '12,580' },
  { label: 'Token用量', value: '8.2M' },
  { label: '活跃用户', value: '32' },
  { label: '日均对话', value: '420' }
]
const usageVisible = ref(false)
const usageLabel = ref('')
const usageData = ref([])
function openUsageDetail(s) {
  usageLabel.value = s.label
  usageData.value = [
    { date: '2026-07-05', value: s.value, note: '今日数据' },
    { date: '2026-07-04', value: Math.floor(Number(s.value.replace(/[^\d]/g,'')) * 0.9), note: '上周同期' },
    { date: '2026-06-05', value: Math.floor(Number(s.value.replace(/[^\d]/g,'')) * 0.7), note: '上月同期' }
  ]
  usageVisible.value = true
}

// ========== RSS新闻源 ==========
const rssDialog = reactive({ visible: false, isEdit: false, form: { name: '', url: '', category: '其他', aiEnabled: true } })
const rssList = ref([])

function openRssDialog(row) {
  if (row) {
    rssDialog.isEdit = true
    Object.assign(rssDialog.form, { name: row.name, url: row.url, category: row.category || '其他', aiEnabled: row.aiEnabled ?? true })
  } else {
    rssDialog.isEdit = false
    Object.assign(rssDialog.form, { name: '', url: '', category: '其他', aiEnabled: true })
  }
  rssDialog.visible = true
}

async function confirmRss() {
  try {
    if (rssDialog.isEdit) {
      await apiPut(`/api/rss/sources/${rssDialog.form.id || encodeURIComponent(rssDialog.form.url)}`, rssDialog.form)
    } else {
      await apiPost('/api/rss/sources', rssDialog.form)
    }
    rssDialog.visible = false
    ElMessage.success('已保存')
    await loadRss()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  }
}

async function deleteRss(row) {
  try {
    await apiDelete(`/api/rss/sources/${row.id || encodeURIComponent(row.url)}`)
    ElMessage.success('已删除')
    await loadRss()
  } catch (e) {
    ElMessage.error('删除失败: ' + (e.message || '未知错误'))
  }
}

async function loadRss() {
  try {
    const res = await apiGet('/api/rss/sources')
    rssList.value = Array.isArray(res) ? res : (res.data || res.sources || [])
  } catch (e) {
    rssList.value = []
  }
}

// ========== 邮箱配置 ==========
const emailConfig = reactive({
  smtpHost: '', smtpPort: 465, smtpUser: '', smtpPass: '',
  fromAddr: '', toAddr: '', sendTime: null, autoSend: false
})

async function saveEmailConfig() {
  try {
    await apiPut('/api/email/config', { ...emailConfig, sendTime: emailConfig.sendTime ? emailConfig.sendTime.toISOString() : null })
    ElMessage.success('邮箱配置已保存')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  }
}

async function testEmail() {
  try {
    await apiPost('/api/email/test', {})
    ElMessage.success('测试邮件发送成功')
  } catch (e) {
    ElMessage.error('测试发送失败: ' + (e.message || '未知错误'))
  }
}

// ========== API 配置 ==========
const selectedApi = ref('dashscope')
const apiServices = [
  { key: 'dashscope', label: '阿里云百炼', desc: '通义千问主力模型' },
  { key: 'deepseek', label: 'DeepSeek', desc: '高性价比模型' },
  { key: 'zhipu', label: '智谱AI (GLM)', desc: '长文本处理' },
  { key: 'moonshot', label: 'Kimi (Moonshot)', desc: '超长上下文' },
  { key: 'minimax', label: 'MiniMax', desc: '创意写作' },
  { key: 'doubao', label: '豆包 (火山引擎)', desc: '低延迟部署' },
  { key: 'aminer', label: 'AMiner 学术', desc: '学者/论文检索' },
  { key: 'vip', label: '维普开放平台', desc: '文献/引文分析' },
  { key: 'asr', label: '音视频转录', desc: 'ASR 语音识别' }
]
const apiConfig = reactive({
  dashscope: { key: '', endpoint: 'https://dashscope.aliyuncs.com/api/v1', models: ['qwen-max', 'qwen-plus'] },
  deepseek: { key: '', baseUrl: 'https://api.deepseek.com', models: ['deepseek-chat'] },
  zhipu: { key: '', baseUrl: 'https://open.bigmodel.cn/api/paas/v4', models: ['glm-4-plus'] },
  moonshot: { key: '', baseUrl: 'https://api.moonshot.cn/v1', models: ['moonshot-v1-32k'] },
  minimax: { groupId: '', key: '', baseUrl: 'https://api.minimax.chat/v1', models: ['abab6.5'] },
  doubao: { key: '', endpoint: 'https://ark.cn-beijing.volces.com/api/v3', models: ['doubao-pro'] },
  aminer: { key: '', baseUrl: 'https://api.aminer.cn', services: ['scholar', 'paper'] },
  vip: { key: '', endpoint: 'https://openapi.cqvip.com', services: ['literature'] },
  asr: { mode: 'aliyun', aliyunKey: '', aliyunSecret: '', aliyunEndpoint: 'https://speech.aliyuncs.com', whisperUrl: 'http://localhost:9000', whisperModel: 'medium', whisperLang: 'zh' }
})

const API = window.location.port === '5173' ? 'http://localhost:8000' : ''

function saveApiConfig() {
  const token = localStorage.getItem('csic_token')
  if (!token) { ElMessage.warning('请先登录'); return }

  const providerMap = {
    dashscope: 'qwen', deepseek: 'deepseek', zhipu: 'zhipu',
    moonshot: 'kimi', minimax: 'minimax', doubao: 'doubao',
    aminer: 'aminer', vip: 'vip', asr: 'asr',
  }

  let success = 0
  Object.entries(providerMap).forEach(([frontKey, backendKey]) => {
    const cfg = apiConfig[frontKey]
    if (!cfg || !cfg.key) return
    fetch(`${API}/api/config/${backendKey}`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ config_json: { ...cfg, key: cfg.key } }),
    }).then(r => { if (r.ok) success++ }).catch(() => {})
  })

  localStorage.setItem('csic_api_configs', JSON.stringify(apiConfig))
  ElMessage.success(`配置已保存（${success} 个服务已同步到后端）`)
}

onMounted(async () => {
  // 加载 API 配置
  const token = localStorage.getItem('csic_token')
  if (token) {
    const backendKeys = ['qwen', 'deepseek', 'zhipu', 'kimi', 'minimax', 'doubao', 'aminer', 'vip', 'asr']
    const frontKeys = ['dashscope', 'deepseek', 'zhipu', 'moonshot', 'minimax', 'doubao', 'aminer', 'vip', 'asr']
    backendKeys.forEach((bk, i) => {
      fetch(`${API}/api/config/${bk}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(r => r.json()).then(data => {
        if (data && data.key) Object.assign(apiConfig[frontKeys[i]], data)
      }).catch(() => {})
    })
  }

  // 加载业务数据
  await Promise.allSettled([
    loadUsers(),
    loadModels(),
    loadRss(),
    fetchIntegrations(),
    fetchKnowledgeBases()
  ])
  ])
})

// API 连接测试
const testing = reactive({ aminer: false, vip: false, dashscope: false, deepseek: false })
const testResult = reactive({ aminer: null, vip: null, dashscope: null, deepseek: null })

async function testAminerApi() {
  if (!apiConfig.aminer.key) { ElMessage.warning('请先填写 API Key'); return }
  testing.aminer = true; testResult.aminer = null
  try {
    const url = apiConfig.aminer.baseUrl + '/api/search/scholar'
    const resp = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiConfig.aminer.key },
      body: JSON.stringify({ query: 'machine learning', size: 1 })
    })
    testResult.aminer = resp.ok
    if (resp.ok) ElMessage.success('AMiner API 连接成功')
    else ElMessage.error('连接失败: ' + resp.status)
  } catch (e) {
    testResult.aminer = false; ElMessage.error('连接异常: ' + e.message)
  } finally { testing.aminer = false }
}

async function testVipApi() {
  if (!apiConfig.vip.key) { ElMessage.warning('请先填写 API Key'); return }
  testing.vip = true; testResult.vip = null
  try {
    const resp = await fetch(apiConfig.vip.endpoint + '/api/v3/search', {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + apiConfig.vip.key },
      signal: AbortSignal.timeout(8000)
    })
    testResult.vip = resp.ok
    if (resp.ok) ElMessage.success('维普 API 连接成功')
    else ElMessage.error('连接失败: ' + resp.status)
  } catch (e) {
    testResult.vip = false; ElMessage.error('连接异常: ' + e.message)
  } finally { testing.vip = false }
}

// ---- Dify / 集成项目管理 ----
const integrations = ref([])
const knowledgeBases = ref([])
const difySync = reactive({ kbId: '' })

async function fetchIntegrations() {
  const token = localStorage.getItem('csic_token')
  if (!token) return
  try {
    const r = await fetch(API + '/api/admin/integrations', { headers: { 'Authorization': 'Bearer ' + token } })
    const d = await r.json()
    integrations.value = d.integrations || []
  } catch(e) {}
}

async function fetchKnowledgeBases() {
  const token = localStorage.getItem('csic_token')
  if (!token) return
  try {
    const r = await fetch(API + '/api/knowledge', { headers: { 'Authorization': 'Bearer ' + token } })
    const d = await r.json()
    knowledgeBases.value = Array.isArray(d) ? d : (d.items || [])
  } catch(e) {}
}

async function fetchDifyDatasets() { /* placeholder */ }

async function syncToDify() {
  const token = localStorage.getItem('csic_token')
  if (!token) return
  try {
    const r = await fetch(API + '/api/dify/sync-knowledge?kb_id=' + difySync.kbId, {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }
    })
    const d = await r.json()
    ElMessage.success(d.message || '同步完成')
  } catch(e) { ElMessage.error('同步失败') }
}
</script>

<style scoped>
.content-card { border-radius: 8px; border: 1px solid var(--border-color); }
.section-toolbar { margin-bottom: 14px; display: flex; justify-content: flex-end; }
.admin-tabs :deep(.el-tabs__item) { font-size: 14px; }

/* API 配置左右分栏 */
.api-split { display: flex; gap: 16px; min-height: 420px; }
.api-split .api-sidebar {
  width: 200px; flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  padding-right: 12px;
}
.api-split .api-svc-item {
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: all .15s;
  margin-bottom: 2px;
}
.api-split .api-svc-item:hover { background: #f6f8fa; }
.api-split .api-svc-item.active {
  background: #f0f5ff;
  border: 1px solid #bae0ff;
}
.api-split .api-svc-name { font-weight: 600; font-size: 13px; color: var(--text-main); }
.api-split .api-svc-desc { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.api-split .api-main { flex: 1; min-width: 0; padding-left: 4px; }
.api-form-title { margin: 0 0 12px; font-size: 16px; font-weight: 700; color: var(--text-main); }
</style>
