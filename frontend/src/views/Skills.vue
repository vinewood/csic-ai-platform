<template>
  <div>
    <div class="csic-hero csic-hero--skills">
      <div class="hero-content"><h2>AI 技能中心</h2><p>预置AI技能 · 自定义技能 · 收藏调用 · {{ skills.length }} 个技能</p></div>
    </div>

    <div class="csic-filter-bar">
      <el-input v-model="search" placeholder="搜索技能..." clearable style="width:240px"><template #prefix><el-icon><Search /></el-icon></template></el-input>
      <el-radio-group v-model="filter" size="small">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button v-for="c in categories" :key="c" :value="c">{{ c }}</el-radio-button>
      </el-radio-group>
      <el-button :type="showFav?'primary':'default'" size="small" :icon="Star" @click="showFav=!showFav" round>{{ showFav?'全部':'收藏' }}</el-button>
      <el-button type="success" size="small" :icon="Plus" @click="openCreate" round style="margin-left:auto">新建技能</el-button>
    </div>

    <el-row :gutter="12">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="4" v-for="s in displayed" :key="s.id" style="margin-bottom:12px">
        <el-card shadow="hover" class="skill-card" @click="openDetail(s)">
          <div class="skill-top">
            <el-button :type="s.favorited?'warning':'default'" :icon="s.favorited?StarFilled:Star" size="small" circle @click.stop="toggleFav(s)" />
          </div>
          <div class="skill-main">
            <div class="skill-icon" :style="{background:hex(s.color,0.08),borderColor:hex(s.color,0.18)}">
              <el-icon :size="24" :color="s.color"><component :is="icons[s.icon]||MenuIcon" /></el-icon>
            </div>
            <div class="skill-info"><h3>{{ s.name }}</h3><p>{{ s.description || '暂无描述' }}</p></div>
          </div>
          <div class="skill-footer">
            <el-tag size="small" effect="light">{{ s.category }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 技能详情弹窗 — 大屏 Markdown 查看 -->
    <el-dialog v-model="detail.visible" :title="detail.skill?.name" width="720px" top="5vh" destroy-on-close>
      <template v-if="detail.skill">
        <div class="detail-meta">
          <el-tag size="small" effect="light">{{ detail.skill.category }}</el-tag>
          <span style="color:#94a3b8;font-size:12px;margin-left:8px">{{ detail.skill.description }}</span>
          <a v-if="detail.skill.github_url" :href="detail.skill.github_url" target="_blank" style="font-size:12px;color:#1677ff;margin-left:8px">GitHub 来源 ↗</a>
        </div>
        <el-divider />
        <div class="markdown-view">
          <div class="md-label">系统提示词</div>
          <div class="md-content">{{ detail.skill.prompt || '暂无提示词' }}</div>
        </div>
      </template>
      <template #footer>
        <div class="detail-footer">
          <el-button @click="editSkill(detail.skill)">修改</el-button>
          <el-button :type="detail.skill?.favorited?'warning':'default'" @click="toggleFav(detail.skill);detail.visible=false">{{ detail.skill?.favorited?'取消收藏':'收藏' }}</el-button>
          <el-button type="primary" @click="useIn('chat')">AI对话使用</el-button>
          <el-button type="success" @click="useIn('teaching')">教学使用</el-button>
          <el-button type="info" @click="useIn('research')">科研使用</el-button>
          <el-button type="danger" @click="delSkill(detail.skill)">删除</el-button>
          <el-button @click="detail.visible=false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新建/编辑技能弹窗 — 大屏 Markdown 编辑 -->
    <el-dialog v-model="create.visible" :title="create.editId?'编辑技能':'新建技能'" width="700px" top="5vh" destroy-on-close>
      <el-form :model="create.form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="create.form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="create.form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="create.form.category" style="width:200px">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
          <el-input v-model="create.form.icon" placeholder="图标名" style="width:140px;margin-left:8px" />
          <el-input v-model="create.form.color" placeholder="颜色" style="width:100px;margin-left:8px" />
        </el-form-item>
        <el-form-item label="提示词">
          <el-input v-model="create.form.prompt" type="textarea" :rows="15" style="font-family:monospace;font-size:12px" placeholder="Markdown/代码模式输入系统提示词..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="create.visible=false">取消</el-button>
        <el-button type="primary" @click="confirmSkill">保存技能</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Star, StarFilled, Plus, Menu as MenuIcon } from '@element-plus/icons-vue'
import * as Icons from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiGet, apiPost, apiPut, apiDelete } from '../api.js'

const router = useRouter()
const icons = { ...Icons }
const search = ref(''), filter = ref(''), showFav = ref(false)
const skills = ref([])
const categories = computed(() => [...new Set(skills.value.map(s=>s.category).filter(Boolean))])

const detail = ref({ visible: false, skill: null })
const create = ref({ visible: false, editId: null, form: { name:'', description:'', category:'科研', icon:'MagicStick', color:'#1677ff', prompt:'' } })

onMounted(async () => {
  const d = await apiGet('/api/skills'); if (d) skills.value = d
})

const displayed = computed(() => {
  let l = skills.value
  if (filter.value) l = l.filter(s => s.category === filter.value)
  if (search.value) l = l.filter(s => s.name.includes(search.value) || (s.description||'').includes(search.value))
  if (showFav.value) l = l.filter(s => s.favorited)
  return l
})

function openDetail(s) { detail.value = { visible: true, skill: { ...s } } }

async function toggleFav(s) {
  const r = await apiPut(`/api/skills/${s.id}/favorite`, {})
  if (r) { s.favorited = r.favorited; const idx = skills.value.findIndex(x=>x.id===s.id); if (idx>=0) skills.value[idx].favorited = r.favorited }
}

function useIn(type) {
  const s = detail.value.skill; if (!s) return
  const map = { chat: '/workspace/chat', teaching: '/workspace/teaching', research: '/workspace/research' }
  detail.value.visible = false
  router.push(`${map[type]}?skill=${s.id}`)
}

async function delSkill(s) {
  try { await ElMessageBox.confirm('确定删除该技能？', '确认', { type: 'warning' }) } catch { return }
  await apiDelete(`/api/skills/${s.id}`)
  skills.value = skills.value.filter(x => x.id !== s.id)
  detail.value.visible = false
  ElMessage.success('已删除')
}

function editSkill(s) { detail.visible = false; create.value = { visible: true, editId: s.id, form: { ...s } } }
function openCreate() { create.value = { visible: true, editId: null, form: { name:'', description:'', category:'科研', icon:'MagicStick', color:'#1677ff', prompt:'' } } }

async function confirmSkill() {
  if (!create.value.form.name) { ElMessage.warning('请输入名称'); return }
  const d = create.value.form
  let r
  if (create.value.editId) {
    r = await apiPut(`/api/skills/${create.value.editId}`, d)
  } else {
    r = await apiPost('/api/skills', d)
  }
  if (r) { create.value.visible = false; const dd = await apiGet('/api/skills'); if (dd) skills.value = dd; ElMessage.success('已保存') }
}

function hex(c, a) { if (!c?.startsWith('#')) return `rgba(22,119,255,${a})`; const r=parseInt(c.slice(1,3),16),g=parseInt(c.slice(3,5),16),b=parseInt(c.slice(5,7),16); return `rgba(${r},${g},${b},${a})` }
</script>

<style scoped>
.skill-card { cursor:pointer; border-radius:10px; border:1px solid #e5e7eb; position:relative; transition:all .15s; }
.skill-card:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,.06); }
.skill-top { position:absolute; top:8px; right:8px; z-index:2; }
.skill-main { display:flex; gap:10px; margin-bottom:10px; }
.skill-icon { width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; border:1px solid; flex-shrink:0; }
.skill-info h3 { margin:0 0 4px; font-size:14px; font-weight:600; }
.skill-info p { color:#94a3b8; font-size:12px; margin:0; line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.skill-footer { display:flex; justify-content:space-between; padding-top:8px; border-top:1px solid #f0f0f0; }

.detail-meta { margin-bottom:8px; }
.markdown-view { background:#1e293b; border-radius:8px; padding:16px; }
.md-label { color:#94a3b8; font-size:11px; text-transform:uppercase; margin-bottom:8px; }
.md-content { color:#e2e8f0; font-family:Consolas,monospace; font-size:13px; line-height:1.7; white-space:pre-wrap; max-height:400px; overflow-y:auto; }
.detail-footer { display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; }
</style>
