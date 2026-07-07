<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1200&q=80);">
      <div class="hero-content">
        <h2>AI 技能中心</h2>
        <p>预置AI技能 · 自定义技能 · 收藏调用</p>
      </div>
    </div>

    <div class="csic-filter-bar">
      <el-input v-model="search" placeholder="搜索技能..." clearable style="width:240px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-radio-group v-model="filter" size="small">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="教学">教学</el-radio-button>
        <el-radio-button value="科研">科研</el-radio-button>
        <el-radio-button value="新闻">新闻</el-radio-button>
        <el-radio-button value="工具">工具</el-radio-button>
      </el-radio-group>
      <el-button :type="showFavOnly?'primary':'default'" size="small" :icon="Star" @click="showFavOnly=!showFavOnly" round>
        {{ showFavOnly ? '全部技能' : '我的收藏' }}
      </el-button>
      <el-button type="success" size="small" :icon="Plus" @click="openCreateDialog" round style="margin-left:auto;">新建技能</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="s in displayed" :key="s.id" style="margin-bottom:16px;">
        <el-card shadow="hover" class="skill-card" @click="useSkill(s)">
          <div class="skill-actions-top">
            <el-button
              :type="s.favorited ? 'warning' : 'default'"
              :icon="s.favorited ? StarFilled : Star"
              size="small"
              circle
              @click.stop="toggleFav(s)"
            />
          </div>
          <div class="skill-main">
            <div class="skill-icon" :style="{background: hexToRgba(s.color, 0.08), borderColor: hexToRgba(s.color, 0.18)}">
              <el-icon :size="26" :color="s.color"><component :is="s.icon || 'MagicStick'" /></el-icon>
            </div>
            <div class="skill-info">
              <h3>{{ s.name }}</h3>
              <p>{{ s.desc }}</p>
            </div>
          </div>
          <div class="skill-footer">
            <el-tag size="small" effect="light" :style="{color: s.color, background: hexToRgba(s.color, 0.08), borderColor: hexToRgba(s.color, 0.15)}">{{ s.category }}</el-tag>
            <span class="skill-stars">★ {{ s.rating }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建技能对话框 -->
    <el-dialog v-model="createVisible" title="新建技能" width="520px" destroy-on-close>
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="技能名称"><el-input v-model="createForm.name" placeholder="输入技能名称" /></el-form-item>
        <el-form-item label="功能描述"><el-input v-model="createForm.desc" type="textarea" :rows="3" placeholder="描述这个技能的功能" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="createForm.category" style="width:100%;">
            <el-option label="科研" value="科研" /><el-option label="教学" value="教学" />
            <el-option label="新闻" value="新闻" /><el-option label="工具" value="工具" />
          </el-select>
        </el-form-item>
        <el-form-item label="系统提示词"><el-input v-model="createForm.prompt" type="textarea" :rows="5" placeholder="定义这个技能的 AI 角色、行为规则和输出格式..." /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible=false">取消</el-button>
        <el-button type="primary" @click="confirmCreate">创建并收藏</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Star, StarFilled, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPost, apiPut } from '../api.js'

const router = useRouter()
const search = ref('')
const filter = ref('')
const showFavOnly = ref(false)
const skills = ref([])

async function loadSkills() {
  const data = await apiGet('/api/skills')
  if (data) skills.value = data
}
onMounted(loadSkills)

const displayed = computed(() => {
  let list = skills.value
  if (filter.value) list = list.filter(s => s.category === filter.value)
  if (search.value) list = list.filter(s => s.name.includes(search.value) || (s.desc || '').includes(search.value))
  if (showFavOnly.value) list = list.filter(s => s.favorited)
  return list
})

async function toggleFav(s) {
  const skillId = s.id.replace('s', '')
  const resp = await apiPut(`/api/skills/${skillId}/favorite`, {})
  if (resp) { s.favorited = resp.favorited; ElMessage.success(resp.favorited ? '已收藏' : '已取消收藏') }
}

// 新建技能
const createVisible = ref(false)
const createForm = ref({ name: '', desc: '', category: '科研', prompt: '' })
function openCreateDialog() { createForm.value = { name: '', desc: '', category: '科研', prompt: '' }; createVisible.value = true }
async function confirmCreate() {
  if (!createForm.value.name) { ElMessage.warning('请输入技能名称'); return }
  const resp = await apiPost('/api/skills', { name: createForm.value.name, desc: createForm.value.desc, category: createForm.value.category, prompt: createForm.value.prompt })
  if (resp) { createVisible.value = false; await loadSkills(); ElMessage.success('技能已创建并自动收藏') }
}

function useSkill(s) { router.push(`/workspace/chat?skill=${s.id}`) }
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
</script>

<style scoped>
.skill-card {
  cursor: pointer;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
  position: relative;
}
.skill-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-card-hover); border-color: var(--el-color-primary-light-7); }
.skill-actions-top { position: absolute; top: 10px; right: 10px; z-index: 2; }
.skill-main { display: flex; gap: 12px; margin-bottom: 14px; }
.skill-icon { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; border: 1px solid; flex-shrink: 0; }
.skill-info { flex: 1; min-width: 0; }
.skill-info h3 { margin: 0 0 6px; font-size: 15px; font-weight: 600; color: var(--text-main); }
.skill-info p { color: var(--text-muted); font-size: 12px; margin: 0; line-height: 1.5; }
.skill-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-color); }
.skill-stars { font-size: 13px; color: #faad14; font-weight: 600; }
</style>
