<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=1200&q=80);">
      <div class="hero-content">
        <h2>知识库</h2>
        <p>教学资料 · 研究成果 · 政策法规</p>
      </div>
    </div>

    <div class="knowledge-layout">
      <div class="kb-sidebar">
        <el-card shadow="never" class="side-card">
          <template #header>
            <div class="side-header">
              <span>知识库列表</span>
              <el-button type="primary" size="small" @click="openNewKb">+ 新建</el-button>
            </div>
          </template>
          <div v-for="kb in kbs" :key="kb.id" :class="['kb-item', { active: selected?.id === kb.id }]" @click="selected = kb">
            <div class="kb-name">{{ kb.name }}</div>
            <div class="kb-meta">{{ kb.type }} · {{ kb.docs }} 文档</div>
            <div class="kb-actions">
              <el-button link type="primary" size="small" @click.stop="editKb(kb)">编辑</el-button>
              <el-popconfirm title="确定删除此知识库？" @confirm="deleteKb(kb.id)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </el-card>
      </div>

      <div class="kb-main">
        <el-card v-if="selected" shadow="never" class="content-card">
          <template #header>
            <div class="main-header">
              <span>{{ selected.name }}</span>
              <el-button type="primary" size="small" @click="uploadVisible = true">上传文档</el-button>
            </div>
          </template>
          <el-table :data="selected.items" stripe>
            <el-table-column prop="title" label="文档名称" min-width="260" />
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" effect="light" :type="fileType(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="date" label="更新时间" width="130" />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="viewDoc(row)">查看</el-button>
                <el-button link type="primary" size="small" @click="editDoc(row)">编辑</el-button>
                <el-popconfirm title="确定删除此文档？" @confirm="deleteDoc(row)">
                  <template #reference>
                    <el-button link type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        <el-card v-else shadow="never" class="empty-card">
          <div class="empty-state">
            <el-icon :size="48" color="#d1d5db"><Collection /></el-icon>
            <p>请选择或新建一个知识库</p>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 新建知识库对话框 -->
    <el-dialog v-model="newKbVisible" title="新建知识库" width="400px" destroy-on-close>
      <el-form :model="newKbForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="newKbForm.name" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="newKbForm.type" style="width:100%;">
            <el-option label="教学" value="教学" />
            <el-option label="科研" value="科研" />
            <el-option label="参考" value="参考" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newKbVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmNewKb">确认</el-button>
      </template>
    </el-dialog>

    <!-- 上传文档对话框 -->
    <el-dialog v-model="uploadVisible" title="上传文档" width="450px" destroy-on-close>
      <el-upload drag :auto-upload="false" style="width:100%;">
        <el-icon :size="36" color="#1677ff"><UploadFilled /></el-icon>
        <p style="font-size:13px;margin:8px 0;">拖拽或点击选择文件</p>
        <p style="font-size:11px;color:#94a3b8;">PDF, Word, Excel, 文本文件</p>
      </el-upload>
      <el-input v-model="uploadTitle" placeholder="文档名称（可选）" style="margin-top:10px;" />
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 查看文档对话框 -->
    <el-dialog v-model="viewVisible" :title="viewDocData?.title" width="600px" destroy-on-close>
      <div class="view-content">
        <p><strong>类型：</strong>{{ viewDocData?.type }}</p>
        <p><strong>更新时间：</strong>{{ viewDocData?.date }}</p>
        <el-divider />
        <p style="color:#94a3b8;line-height:1.8;">文档内容预览区域。在实际系统中这里会展示文档的全文内容或链接。</p>
      </div>
    </el-dialog>

    <!-- 编辑文档对话框 -->
    <el-dialog v-model="editDocVisible" title="编辑文档" width="450px" destroy-on-close>
      <el-form :model="editDocData" label-width="80px">
        <el-form-item label="名称"><el-input v-model="editDocData.title" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="editDocData.type" style="width:100%;">
            <el-option label="PDF" value="PDF" /><el-option label="Word" value="Word" /><el-option label="Excel" value="Excel" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDocVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEditDoc">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑知识库 -->
    <el-dialog v-model="editKbVisible" title="编辑知识库" width="400px" destroy-on-close>
      <el-form :model="editKbForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="editKbForm.name" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editKbForm.type" style="width:100%;">
            <el-option label="教学" value="教学" /><el-option label="科研" value="科研" /><el-option label="参考" value="参考" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editKbVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEditKb">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Collection, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPost, apiPut, apiDelete, apiUpload } from '../api.js'

const selected = ref(null)
const kbs = ref([])

// 加载知识库
async function loadKbs() {
  const data = await apiGet('/api/knowledge')
  if (data) kbs.value = data
}
onMounted(loadKbs)

function fileType(type) {
  const ext = (type || '').toLowerCase()
  if (ext.includes('pdf')) return 'danger'
  if (ext.includes('doc') || ext.includes('word')) return 'primary'
  if (ext.includes('xls') || ext.includes('excel')) return 'success'
  return 'info'
}

// 新建知识库
const newKbVisible = ref(false)
const newKbForm = reactive({ name: '', description: '', type: '教学' })
function openNewKb() { newKbForm.name = ''; newKbForm.description = ''; newKbForm.type = '教学'; newKbVisible.value = true }
async function confirmNewKb() {
  const resp = await apiPost('/api/knowledge', { name: newKbForm.name, description: newKbForm.description, type: newKbForm.type })
  if (resp) { newKbVisible.value = false; await loadKbs(); ElMessage.success('知识库已创建') }
}

// 编辑知识库
const editKbVisible = ref(false)
const editKbForm = reactive({ id: null, name: '', description: '', type: '' })
function editKb(kb) { editKbForm.id = kb.id; editKbForm.name = kb.name; editKbForm.description = kb.description || ''; editKbForm.type = kb.type; editKbVisible.value = true }
async function confirmEditKb() {
  await apiPut(`/api/knowledge/${editKbForm.id}`, { name: editKbForm.name, description: editKbForm.description, type: editKbForm.type })
  editKbVisible.value = false; await loadKbs(); ElMessage.success('已保存')
}
async function deleteKb(id) {
  await apiDelete(`/api/knowledge/${id}`)
  if (selected.value?.id === id) selected.value = null
  await loadKbs(); ElMessage.success('已删除')
}

// 上传
const uploadVisible = ref(false)
const uploadFileObj = ref(null)
const uploadTitle = ref('')
function onFileSelected(file) { uploadFileObj.value = file.raw; uploadTitle.value = file.name }
async function confirmUpload() {
  if (!selected.value || !uploadFileObj.value) { ElMessage.warning('请选择知识库和文件'); return }
  const form = new FormData()
  form.append('file', uploadFileObj.value)
  form.append('title', uploadTitle.value)
  const resp = await apiUpload(`/api/knowledge/${selected.value.id}/docs`, form)
  if (resp) { uploadVisible.value = false; await loadKbs(); ElMessage.success('上传成功') }
}

// 查看文档
const viewVisible = ref(false)
const viewDocData = ref(null)
function viewDoc(row) { viewDocData.value = row; viewVisible.value = true }

// 编辑文档
const editDocVisible = ref(false)
const editDocData = ref({})
function editDoc(row) { editDocData.value = { ...row }; editDocVisible.value = true }
async function confirmEditDoc() {
  if (!selected.value) return
  await apiPut(`/api/knowledge/${selected.value.id}/docs/${editDocData.value.id}`, { title: editDocData.value.title })
  editDocVisible.value = false; await loadKbs(); ElMessage.success('文档已更新')
}
async function deleteDoc(row) {
  if (!selected.value) return
  await apiDelete(`/api/knowledge/${selected.value.id}/docs/${row.id}`)
  await loadKbs(); ElMessage.success('已删除')
}
</script>

<style scoped>
.knowledge-layout { display: flex; gap: 14px; }
.kb-sidebar { width: 280px; flex-shrink: 0; }
.kb-main { flex: 1; min-width: 0; }
.side-card, .content-card, .empty-card { border-radius: 8px; border: 1px solid var(--border-color); }
.side-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.main-header { display: flex; justify-content: space-between; align-items: center; }
.kb-item { padding: 10px 12px; cursor: pointer; border-radius: 6px; margin-bottom: 2px; transition: all .15s; border: 1px solid transparent; }
.kb-item:hover { background: #f6f8fa; }
.kb-item.active { background: #f0f5ff; border-color: #bae0ff; }
.kb-name { font-weight: 500; font-size: 14px; color: var(--text-main); margin-bottom: 3px; }
.kb-meta { font-size: 12px; color: var(--text-muted); }
.kb-actions { margin-top: 6px; display: none; }
.kb-item:hover .kb-actions { display: flex; gap: 4px; }
.empty-state { text-align: center; padding: 80px 0; color: #94a3b8; }
.empty-state p { margin-top: 12px; }
.view-content { line-height: 1.8; }

@media (max-width: 768px) { .knowledge-layout { flex-direction: column; } .kb-sidebar { width: 100%; } }
</style>
