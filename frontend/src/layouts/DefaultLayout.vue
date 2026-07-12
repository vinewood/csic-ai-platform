<template>
  <div class="vben-layout">
    <!-- Top Header — 深蓝渐变 + 粒子 -->
    <header ref="headerEl" class="vben-header">
      <div class="bar-inner">
        <div class="vben-header-left">
          <div class="brand-mark">
            <img src="/img/logo-en.png" alt="CSIC" class="header-logo-en" />
            <div class="brand-divider"></div>
            <div class="brand-text-group">
              <span class="brand-text">中船党校</span>
              <span class="brand-sub">AI助手</span>
            </div>
          </div>
        </div>
        <div class="vben-header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-avatar :size="30" icon="UserFilled" class="user-avatar" />
              <span class="user-name">{{ userName }}</span>
              <el-icon class="user-arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="profileVisible = true">个人设置</el-dropdown-item>
                <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- Tab navigation, inside header -->
      <div class="bar-inner tabs-inner">
        <div
          v-for="tab in visibleTabs"
          :key="tab.path"
          :class="['vben-tab', { active: isActive(tab) }]"
          @click="$router.push(tab.fullPath)"
        >
          <el-icon v-if="tab.meta?.icon" class="tab-icon">
            <component :is="tab.meta.icon" />
          </el-icon>
          <span class="tab-title">{{ tab.meta?.title }}</span>
        </div>
      </div>
    </header>

    <!-- Content -->
    <main class="vben-content">
      <div class="content-inner">
        <router-view />
      </div>
    </main>

    <!-- 个人设置对话框 -->
    <el-dialog v-model="profileVisible" title="个人设置" width="500px" destroy-on-close>
      <el-form :model="profileForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input :model-value="userName" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="your@email.com" />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="profileForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="profileForm.password" type="password" placeholder="留空不修改密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <el-button type="primary" :loading="profileLoading" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPut } from '../api.js'

const route = useRoute()
const router = useRouter()
const headerEl = ref(null)

const userInfo = reactive({ name: '', role: '', email: '', real_name: '' })

// 从 localStorage 初始化 + API 获取真实角色
onMounted(async () => {
  try {
    const cached = JSON.parse(localStorage.getItem('csic_user') || '{}')
    if (cached.name) Object.assign(userInfo, cached)
  } catch {}
  // 从后端获取最新角色信息
  const me = await apiGet('/api/auth/me')
  if (me) {
    Object.assign(userInfo, me)
    localStorage.setItem('csic_user', JSON.stringify(userInfo))
  }
})

const userName = computed(() => userInfo.name || '管理员')
const userRole = computed(() => userInfo.role || 'user')

const tabs = computed(() => {
  const parent = route.matched.find(r => r.path === '/workspace')
  return (parent?.children || [])
    .filter(child => !child.meta?.hidden)
    .map(child => ({ ...child, fullPath: '/workspace/' + child.path }))
})

// 非管理员隐藏系统管理tab
const visibleTabs = computed(() => {
  if (userRole.value === 'admin') return tabs.value
  return tabs.value.filter(t => t.meta?.title !== '系统管理')
})

function isActive(tab) { return route.path === tab.fullPath }
function logout() { localStorage.removeItem('csic_token'); localStorage.removeItem('csic_user'); router.push('/') }

// 个人设置
const profileVisible = ref(false)
const profileLoading = ref(false)
const profileForm = reactive({ email: '', real_name: '', password: '' })

onMounted(() => {
  const u = userInfo
  profileForm.email = u.email || ''
  profileForm.real_name = u.real_name || ''
})

async function saveProfile() {
  profileLoading.value = true
  try {
    const body = {}
    if (profileForm.email) body.email = profileForm.email
    if (profileForm.password) body.password = profileForm.password
    if (profileForm.real_name) body.real_name = profileForm.real_name
    await apiPut('/api/auth/me/profile', body)
    ElMessage.success('个人信息已更新')
    profileVisible.value = false
    // 更新缓存
    const u = userInfo
    if (profileForm.email) u.email = profileForm.email
    if (profileForm.real_name) u.real_name = profileForm.real_name
    localStorage.setItem('csic_user', JSON.stringify(u))
  } catch (e) {
    ElMessage.error(e.message || '更新失败')
  }
  profileLoading.value = false
}

onMounted(() => {
  const s = document.createElement('script')
  s.src = '/js/ocean-particles.js'
  s.onload = () => {
    if (window.OceanParticles && headerEl.value) {
      new OceanParticles(headerEl.value, {
        count: 30, speedMin: 0.12, speedMax: 0.5,
        opacityMin: 0.06, opacityMax: 0.25, sizeMin: 1, sizeMax: 2.5,
        flowDirection: 'right', zIndex: 0,
        colors: ['rgba(34,211,238,{o})', 'rgba(8,145,178,{o})', 'rgba(212,168,67,{o})']
      })
    }
  }
  document.head.appendChild(s)
})
</script>

<style scoped>
.vben-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-page);
}

/* Header */
.vben-header {
  position: relative;
  height: 104px;
  flex-shrink: 0;
  z-index: 100;
  overflow: hidden;
  background: linear-gradient(135deg, #050d1a 0%, #0a1628 30%, #0f2347 60%, #1a365d 100%);
  box-shadow: none;
}

.bar-inner {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 58px;
  top: 0;
  z-index: 1;
}

.vben-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.25), transparent);
}

.tabs-inner {
  top: auto;
  bottom: 0;
  height: 46px;
  justify-content: flex-start;
  gap: 6px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

/* 左侧品牌区 */
.vben-header-left {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 1;
  margin-right: auto;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.header-logo-en {
  height: 30px;
  width: auto;
  filter: brightness(0) invert(1) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  display: block;
}

.brand-divider {
  width: 1px;
  height: 22px;
  background: rgba(255, 255, 255, 0.2);
}

.brand-text-group {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.brand-text {
  font-size: 17px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
}

.brand-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  font-weight: 500;
  padding: 3px 8px;
  background: rgba(34, 211, 238, 0.12);
  border: 1px solid rgba(34, 211, 238, 0.22);
  border-radius: 20px;
  letter-spacing: 0.5px;
}

/* 右侧用户区 */
.vben-header-right {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 1;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 24px;
  transition: background var(--transition-fast);
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.08);
}

.user-avatar {
  border: 2px solid rgba(255, 255, 255, 0.15);
  background: linear-gradient(135deg, #22d3ee 0%, #1677ff 100%) !important;
}

.user-name {
  margin-left: 8px;
  color: #fff;
  font-weight: 500;
}

.user-arrow {
  margin-left: 5px;
  color: rgba(255, 255, 255, 0.55);
}

/* Tab */
.vben-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
  font-weight: 500;
  border: 1px solid transparent;
}

.vben-tab:hover {
  color: #fff;
  background: rgba(255,255,255,0.14);
}

.vben-tab.active {
  color: #fff;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 3px 10px rgba(22, 119, 255, 0.35);
}

.tab-icon {
  font-size: 15px;
}

.tab-title {
  line-height: 1;
}

/* Content */
.vben-content {
  flex: 1;
  padding: 20px 24px 28px;
  overflow-y: auto;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: calc(100vh - 104px);
}

.content-inner {
  max-width: 1440px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .vben-header { height: 90px; }
  .bar-inner { padding: 0 16px; }
  .header-logo-en { height: 24px; }
  .brand-divider { height: 18px; }
  .brand-text { font-size: 14px; }
  .brand-sub { font-size: 10px; padding: 2px 6px; }
  .vben-tab { padding: 6px 12px; font-size: 12px; }
  .vben-content { padding: 14px 16px 20px; }
}
</style>
