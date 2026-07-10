<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=1200&q=80);">
      <div class="hero-content"><h2>知识库</h2><p>AI 知识库管理 · 文档上传 · RAG 增强检索</p></div>
    </div>
    <el-card shadow="never" style="margin:12px 16px;border-radius:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <el-button type="primary" :icon="Plus" @click="createVisible=true">新建知识库</el-button>
        <span style="color:#94a3b8;font-size:13px">共 {{ kbs.length }} 个知识库</span>
      </div>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" v-for="kb in kbs" :key="kb.id" style="margin-bottom:16px">
          <el-card shadow="hover" class="kb-card" @click="openKb(kb)">
            <h4>{{ kb.name }}</h4>
            <p>{{ kb.description || '暂无描述' }}</p>
            <el-tag size="small" effect="light">{{ kb.type || '通用' }}</el-tag>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-dialog v-model="createVisible" title="新建知识库" width="480px">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="newKb.name" placeholder="知识库名称" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="newKb.desc" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newKb.type" style="width:100%">
            <el-option v-for="t in typeList" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible=false">取消</el-button>
        <el-button type="primary" @click="doCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { apiGet, apiPost } from '../api.js'
import { ElMessage } from 'element-plus'

const kbs = ref([]), createVisible = ref(false), typeList = ['党建','教学','技术','政策','综合']
const newKb = ref({ name:'', desc:'', type:'综合' })

onMounted(async () => {
  const d = await apiGet('/api/knowledge')
  if (d) kbs.value = Array.isArray(d) ? d : (d.items || [])
})

function openKb(kb) { ElMessage.info('知识库: ' + kb.name) }
async function doCreate() {
  if (!newKb.value.name) { ElMessage.warning('请输入名称'); return }
  const r = await apiPost('/api/knowledge', newKb.value)
  if (r) { createVisible.value = false; const d = await apiGet('/api/knowledge'); if (d) kbs.value = Array.isArray(d) ? d : [] }
}
</script>

<style scoped>
.kb-card { cursor:pointer; border-radius:10px; border:1px solid #e5e7eb; }
.kb-card:hover { border-color:#1677ff; box-shadow:0 4px 12px rgba(22,119,255,.1); }
.kb-card h4 { margin:0 0 8px; font-size:15px; color:#1f2937; }
.kb-card p { color:#94a3b8; font-size:13px; margin:0 0 8px; }
</style>
