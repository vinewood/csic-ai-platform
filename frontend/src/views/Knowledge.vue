<template>
  <div>
    <div class="kb-topbar">
      <div class="kb-title">知识库 <span class="kb-sub">— Dify AI 知识引擎</span></div>
      <div style="display:flex;gap:6px">
        <el-button size="small" text @click="refresh">刷新</el-button>
        <el-button size="small" type="primary" :icon="Plus" @click="showCreate=true">新建数据集</el-button>
      </div>
    </div>

    <div class="kb-body">
      <div class="kb-stats" v-if="datasets.length">
        <span>{{ datasets.length }} 个数据集</span>
        <span>{{ totalDocs }} 个文档</span>
        <span class="stat-dify">Dify 引擎</span>
      </div>

      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" v-for="ds in datasets" :key="ds.id" style="margin-bottom:16px">
          <el-card shadow="hover" class="kb-card" @click="openDataset(ds)">
            <div class="kb-card-hd">
              <el-avatar :size="36" style="background:#1677ff12;color:#1677ff">{{ ds.name?.[0] }}</el-avatar>
              <div style="flex:1;min-width:0">
                <h4>{{ ds.name }}</h4>
                <span class="kb-meta">{{ ds.document_count || 0 }} 文档 · {{ ds.word_count ? (ds.word_count/1000).toFixed(0)+'K字' : '空' }}</span>
              </div>
              <el-dropdown trigger="click" @command="(cmd)=>dsAction(cmd,ds)" @click.stop>
                <el-button link size="small"><el-icon><MoreFilled /></el-icon></el-button>
                <template #dropdown><el-dropdown-menu>
                  <el-dropdown-item command="upload">上传文档</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除数据集</el-dropdown-item>
                </el-dropdown-menu></template>
              </el-dropdown>
            </div>
            <p v-if="ds.description">{{ ds.description }}</p>
            <div style="display:flex;gap:4px;margin-top:6px">
              <el-tag size="small" effect="light">{{ ds.permission || '私有' }}</el-tag>
              <el-tag v-if="ds.indexing_technique" size="small" effect="light" type="info">{{ ds.indexing_technique }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 内置知识库 -->
      <div v-if="localKbs.length" style="margin-top:8px">
        <div style="font-size:11px;color:#bbb;margin-bottom:8px;font-weight:600">内置知识库</div>
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="8" v-for="kb in localKbs" :key="kb.id" style="margin-bottom:16px">
            <el-card shadow="hover" class="kb-card">
              <div class="kb-card-hd">
                <el-avatar :size="36" style="background:#f0f5ff;color:#1677ff">{{ kb.name?.[0] }}</el-avatar>
                <div><h4>{{ kb.name }}</h4><span class="kb-meta">{{ kb.description || '' }}</span></div>
              </div>
              <el-tag size="small" effect="light">{{ kb.type || kb.category || '通用' }}</el-tag>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 空状态 -->
      <div v-if="!datasets.length && !localKbs.length" class="kb-empty">
        <div class="csic-empty">
          <span class="empty-icon">📚</span>
          <span class="empty-title">暂无数据集</span>
          <span class="empty-desc">点击右上角「新建数据集」，上传文档后即可在对话中挂载知识库</span>
        </div>
        <el-button type="primary" size="small" style="margin-top:12px" @click="showCreate=true">新建数据集</el-button>
      </div>
    </div>

    <!-- 创建对话框 -->
    <el-dialog v-model="showCreate" title="新建数据集" width="450px" destroy-on-close>
      <el-form label-width="60px" @submit.prevent="doCreate">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="数据集名称" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.desc" type="textarea" :rows="3" placeholder="描述（可选）" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="doCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 数据集详情对话框 -->
    <el-dialog v-model="showDetail" :title="detailDs?.name" width="700px" destroy-on-close>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <span style="font-size:13px;color:#6b7280">{{ detailDs?.description || '暂无描述' }}</span>
        <el-upload :show-file-list="false" :before-upload="(f)=>{uploadDoc(f);return false}" accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx" v-if="detailDs">
          <el-button size="small" type="primary">上传文档</el-button>
        </el-upload>
      </div>
      <el-table :data="detailDocs" stripe size="small" v-loading="docsLoading">
        <el-table-column prop="name" label="文档" min-width="180"><template #default="{row}">{{ row.name }}</template></el-table-column>
        <el-table-column label="状态/进度" width="180">
          <template #default="{row}">
            <div style="display:flex;align-items:center;gap:6px">
              <el-tag size="small" :type="statusType(row.status || row.display_status || row.indexing_status)">
                {{ statusLabel(row.status || row.display_status || row.indexing_status) }}
              </el-tag>
              <el-progress v-if="row.status==='indexing'" :percentage="row.progress||10" :stroke-width="4" style="width:60px" :show-text="false" />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="80"><template #default="{row}">{{ row.file_size ? (row.file_size/1024).toFixed(0)+'KB' : '-' }}</template></el-table-column>
        <el-table-column label="操作" width="70"><template #default="{row}"><el-popconfirm title="删除此文档？" @confirm="delDoc(row.id)"><template #reference><el-button link type="danger" size="small">删除</el-button></template></el-popconfirm></template></el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, MoreFilled } from '@element-plus/icons-vue'
import { apiGet, apiDelete, apiPost } from '../api.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const datasets = ref([])
const localKbs = ref([])
const totalDocs = ref(0)
const showCreate = ref(false)
const creating = ref(false)
const form = ref({ name: '', desc: '' })

// Detail
const showDetail = ref(false)
const detailDs = ref(null)
const detailDocs = ref([])
const docsLoading = ref(false)

async function refresh() {
  try {
    const res = await apiGet('/api/dify/datasets')
    if (res && res.data) {
      datasets.value = res.data
      totalDocs.value = res.data.reduce((s, d) => s + (d.document_count || 0), 0)
    }
  } catch (e) { /* Dify not available */ }

  try {
    const res = await apiGet('/api/knowledge')
    localKbs.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) {}
}

async function doCreate() {
  if (!form.value.name) { ElMessage.warning('请输入名称'); return }
  creating.value = true
  try {
    await apiPost(`/api/dify/datasets/create?name=${encodeURIComponent(form.value.name)}&description=${encodeURIComponent(form.value.desc)}`)
    ElMessage.success('数据集已创建')
    showCreate.value = false
    form.value = { name: '', desc: '' }
    await refresh()
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.message || '未知错误'))
  }
  creating.value = false
}

async function openDataset(ds) {
  detailDs.value = ds
  showDetail.value = true
  docsLoading.value = true
  try {
    const res = await apiGet(`/api/dify/datasets/${ds.id}/documents`)
    detailDocs.value = res?.data || []
  } catch (e) {
    detailDocs.value = []
  }
  docsLoading.value = false
}

async function uploadDoc(file) {
  if (!detailDs.value) return
  const fd = new FormData()
  fd.append('file', file)
  docsLoading.value = true
  try {
    const token = localStorage.getItem('csic_token')
    const B = location.port === '5173' ? 'http://localhost:8000' : ''
    const r = await fetch(`${B}/api/dify/datasets/${detailDs.value.id}/documents/upload`, {
      method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd
    })
    const result = await r.json()
    ElMessage.success(`上传成功: ${result.name}，正在处理中...`)
    await refresh()
    await openDataset(detailDs.value)

    // Poll for progress
    if (result.id) {
      let attempts = 0
      const poll = setInterval(async () => {
        if (attempts++ > 30) { clearInterval(poll); return }
        try {
          const s = await apiGet(`/api/dify/documents/${result.id}/status`)
          if (s && (s.status === 'completed' || s.status === 'error')) {
            clearInterval(poll)
            if (s.status === 'completed') ElMessage.success(`✓ ${s.name} 处理完成`)
            else ElMessage.error(`✗ ${s.name}: ${s.error || '处理失败'}`)
            await openDataset(detailDs.value); await refresh()
          }
        } catch {}
      }, 2000)
    }
  } catch (e) {
    ElMessage.error('上传失败: ' + (e.message || ''))
  }
  docsLoading.value = false
}

function statusLabel(s) {
  const map = { completed: '已完成', ready: '就绪', indexing: '处理中', pending: '等待中', error: '失败', stored: '已存储', waiting: '等待中' }
  return map[s] || s || '未知'
}
function statusType(s) {
  if (s === 'completed' || s === 'ready') return 'success'
  if (s === 'indexing' || s === 'pending') return 'warning'
  if (s === 'error') return 'danger'
  return 'info'
}

async function delDoc(docId) {
  try {
    await apiDelete(`/api/dify/datasets/${detailDs.value.id}/documents/${docId}`)
    ElMessage.success('已删除')
    await openDataset(detailDs.value)
    await refresh()
  } catch (e) { ElMessage.error('删除失败') }
}

async function dsAction(cmd, ds) {
  if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(`确定删除数据集「${ds.name}」？此操作不可撤销。`, '确认删除', { type: 'warning' })
      await apiDelete(`/api/dify/datasets/${ds.id}`)
      ElMessage.success('已删除')
      await refresh()
    } catch {}
  } else if (cmd === 'upload') {
    openDataset(ds)
  }
}

onMounted(refresh)
</script>

<style scoped>
.kb-topbar{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#fff;border-bottom:1px solid #e5e7eb}
.kb-title{font-size:16px;font-weight:700;color:#1f2937}
.kb-sub{font-size:12px;color:#94a3b8;font-weight:400}
.kb-body{padding:16px}
.kb-stats{display:flex;gap:20px;margin-bottom:16px;padding:10px 16px;background:#f0f5ff;border-radius:8px;font-size:13px;color:#374151}
.stat-dify{color:#1677ff;font-weight:600;margin-left:auto}
.kb-card{cursor:pointer;border-radius:10px;border:1px solid #e5e7eb;transition:all .15s}
.kb-card:hover{border-color:#1677ff;box-shadow:0 4px 12px rgba(22,119,255,.1)}
.kb-card-hd{display:flex;align-items:center;gap:10px}
.kb-card h4{margin:0;font-size:15px;color:#1f2937;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kb-card p{color:#6b7280;font-size:13px;margin:6px 0 0;line-height:1.5}
.kb-meta{font-size:11px;color:#94a3b8}
.kb-empty{text-align:center;padding:60px 20px}
</style>
