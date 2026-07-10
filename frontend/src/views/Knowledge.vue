<template>
  <div>
    <div class="kb-topbar">
      <div class="kb-title">知识库 <span style="font-size:12px;color:#94a3b8;font-weight:400">— Dify AI 知识引擎</span></div>
      <div style="display:flex;gap:8px;align-items:center">
        <el-button size="small" @click="refreshDify">刷新</el-button>
        <el-button size="small" type="primary" @click="openDify">管理知识库</el-button>
      </div>
    </div>

    <!-- Dify 数据集列表（从后端代理获取） -->
    <div class="kb-body">
      <div class="kb-stats" v-if="datasets.length">
        <div class="stat-item"><span class="stat-num">{{ datasets.length }}</span> 个数据集</div>
        <div class="stat-item"><span class="stat-num">{{ totalDocs }}</span> 个文档</div>
        <div class="stat-item">引擎 <span class="stat-num">Dify</span></div>
      </div>

      <el-row :gutter="16" v-if="datasets.length">
        <el-col :xs="24" :sm="12" :md="8" v-for="ds in datasets" :key="ds.id" style="margin-bottom:16px">
          <el-card shadow="hover" class="kb-card" @click="openDataset(ds)">
            <div class="kb-card-header">
              <el-avatar :size="36" style="background:#1677ff12;color:#1677ff;font-size:16px">{{ ds.name?.[0] || 'K' }}</el-avatar>
              <div>
                <h4>{{ ds.name }}</h4>
                <span style="font-size:11px;color:#94a3b8">{{ ds.document_count || 0 }} 文档 · {{ ds.word_count ? (ds.word_count/1000).toFixed(0)+'K 字' : '空' }}</span>
              </div>
            </div>
            <p v-if="ds.description">{{ ds.description }}</p>
            <div style="display:flex;gap:4px;margin-top:8px;flex-wrap:wrap">
              <el-tag size="small" effect="light">{{ ds.permission || '私有' }}</el-tag>
              <el-tag v-if="ds.embedding_model" size="small" effect="light" type="info">{{ ds.embedding_model }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 内置知识库 -->
      <div v-if="localKbs.length">
        <div style="font-size:11px;color:#bbb;margin:16px 0 8px;font-weight:600">内置知识库</div>
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="8" v-for="kb in localKbs" :key="kb.id" style="margin-bottom:16px">
            <el-card shadow="hover" class="kb-card">
              <div class="kb-card-header">
                <el-avatar :size="36" :style="{background:kb.color||'#f0f5ff',color:'#1677ff',fontSize:'16px'}">{{ kb.name?.[0] || 'K' }}</el-avatar>
                <div>
                  <h4>{{ kb.name }}</h4>
                  <span style="font-size:11px;color:#94a3b8">{{ kb.description || '' }}</span>
                </div>
              </div>
              <el-tag size="small" effect="light">{{ kb.type || kb.category || '通用' }}</el-tag>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 空状态 -->
      <div v-if="!datasets.length && !localKbs.length" class="kb-empty">
        <el-icon :size="48" style="color:#d4d4d8"><component :is="Folder" /></el-icon>
        <p style="color:#999;margin-top:12px">Dify 知识库引擎已就绪</p>
        <p style="color:#bbb;font-size:12px">点击「管理知识库」进入 Dify 创建您的第一个知识库<br>支持 PDF/Word/TXT/Markdown 文档上传与 RAG 检索</p>
        <el-button type="primary" size="small" style="margin-top:16px" @click="openDify">打开 Dify 知识库管理</el-button>
      </div>
    </div>

    <!-- Dify iframe（全屏模式） -->
    <el-dialog v-model="difyVisible" title="Dify 知识库管理" :fullscreen="true" destroy-on-close>
      <div style="height:calc(100vh - 80px);width:100%;overflow:hidden">
        <iframe :src="difyUrl" style="width:100%;height:100%;border:none" 
          @load="onDifyLoad"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Folder } from '@element-plus/icons-vue'
import { apiGet } from '../api.js'
import { ElMessage } from 'element-plus'

const datasets = ref([])
const localKbs = ref([])
const totalDocs = ref(0)
const difyVisible = ref(false)
const difyUrl = ref('/dify/')

async function loadDatasets() {
  // 从 Dify console API 获取数据集列表
  try {
    const res = await apiGet('/api/dify/datasets?page=1&limit=20')
    if (res && res.data) {
      datasets.value = res.data
      totalDocs.value = res.data.reduce((sum, d) => sum + (d.document_count || 0), 0)
    }
  } catch (e) {
    // Dify 可能未初始化，静默处理
  }

  // 同时加载本地知识库
  try {
    const res = await apiGet('/api/knowledge')
    localKbs.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) {}
}

function openDify() {
  difyVisible.value = true
  difyUrl.value = '/dify/?_t=' + Date.now() // 加时间戳防缓存
}

function openDataset(ds) {
  ElMessage.info(`打开数据集: ${ds.name}`)
}

function onDifyLoad() {
  // Dify iframe 加载完成
}

async function refreshDify() {
  ElMessage.success('已刷新')
  await loadDatasets()
}

onMounted(() => {
  loadDatasets()
})
</script>

<style scoped>
.kb-topbar{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#fff;border-bottom:1px solid #e5e7eb}
.kb-title{font-size:16px;font-weight:700;color:#1f2937}
.kb-body{padding:16px}
.kb-stats{display:flex;gap:24px;margin-bottom:16px;padding:10px 16px;background:#f0f5ff;border-radius:8px;font-size:13px;color:#374151}
.stat-num{font-weight:700;color:#1677ff;margin-right:4px}
.kb-card{cursor:pointer;border-radius:10px;border:1px solid #e5e7eb;transition:all .15s}
.kb-card:hover{border-color:#1677ff;box-shadow:0 4px 12px rgba(22,119,255,.1)}
.kb-card-header{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.kb-card h4{margin:0;font-size:15px;color:#1f2937}
.kb-card p{color:#6b7280;font-size:13px;margin:4px 0;line-height:1.5}
.kb-empty{text-align:center;padding:60px 20px}
</style>
