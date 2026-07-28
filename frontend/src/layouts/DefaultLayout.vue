<template>
  <div class="vben-layout">
    <!-- Top Header -->
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
          <!-- Desktop tabs -->
          <div class="desktop-tabs">
            <div v-for="tab in visibleTabs" :key="tab.path" :class="['vben-tab', { active: isActive(tab) }]" @click="$router.push(tab.fullPath)">
              <el-icon v-if="tab.meta?.icon" class="tab-icon"><component :is="tab.meta.icon" /></el-icon>
              <span class="tab-title">{{ tab.meta?.title }}</span>
            </div>
          </div>
          <!-- 帮助中心 / 接口文档 快捷入口 -->
          <div class="header-links">
            <el-tooltip content="帮助中心" placement="bottom">
              <a class="header-link" href="/help/" target="_blank" rel="noopener">
                <el-icon :size="17"><QuestionFilled /></el-icon><span class="link-text">帮助</span>
              </a>
            </el-tooltip>
            <el-tooltip content="接口文档（ReDoc）" placement="bottom">
              <a class="header-link" href="/redoc" target="_blank" rel="noopener">
                <el-icon :size="17"><Reading /></el-icon><span class="link-text">接口</span>
              </a>
            </el-tooltip>
          </div>
          <!-- User dropdown -->
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
          <!-- Hamburger for mobile -->
          <el-button class="hamburger-btn" text @click="drawerOpen = true">
            <el-icon :size="22"><Menu /></el-icon>
          </el-button>
        </div>
      </div>
    </header>

    <!-- Content -->
    <main class="vben-content">
      <div class="content-inner">
        <router-view />
      </div>
    </main>

    <!-- Mobile drawer -->
    <el-drawer v-model="drawerOpen" direction="rtl" size="220px" :with-header="false">
      <div class="mobile-nav">
        <div class="mobile-nav-title">菜单导航</div>
        <div v-for="tab in visibleTabs" :key="tab.path" :class="['mobile-nav-item', { active: isActive(tab) }]" @click="navTo(tab)">
          <el-icon v-if="tab.meta?.icon" :size="16"><component :is="tab.meta.icon" /></el-icon>
          <span>{{ tab.meta?.title }}</span>
        </div>
        <el-divider />
        <div class="mobile-nav-item" @click="profileVisible = true; drawerOpen = false">
          <el-icon :size="16"><UserFilled /></el-icon>
          <span>个人设置</span>
        </div>
        <div class="mobile-nav-item" @click="logout">
          <el-icon :size="16"><SwitchButton /></el-icon>
          <span>退出登录</span>
        </div>
      </div>
    </el-drawer>

    <!-- Profile dialog -->
    <el-dialog v-model="profileVisible" title="个人设置" width="400px" destroy-on-close>
      <el-form :model="profileForm" label-width="80px">
        <el-form-item label="用户名"><el-input :model-value="userName" disabled /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="profileForm.email" placeholder="your@email.com" /></el-form-item>
        <el-form-item label="真实姓名"><el-input v-model="profileForm.real_name" placeholder="请输入真实姓名" /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="profileForm.password" type="password" placeholder="留空不修改密码" show-password /></el-form-item>
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
import { ArrowDown, UserFilled, Menu, SwitchButton, QuestionFilled, Reading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPut } from '../api.js'

const route = useRoute()
const router = useRouter()
const headerEl = ref(null)

const drawerOpen = ref(false)
const userInfo = reactive({ name: '', role: '', email: '', real_name: '' })

onMounted(async () => {
  try {
    const cached = JSON.parse(localStorage.getItem('csic_user') || '{}')
    if (cached.name) Object.assign(userInfo, cached)
  } catch {}
  const me = await apiGet('/api/auth/me')
  if (me) { Object.assign(userInfo, me); localStorage.setItem('csic_user', JSON.stringify(userInfo)) }
})

const userName = computed(() => userInfo.name || '管理员')
const userRole = computed(() => userInfo.role || 'user')

const tabs = computed(() => {
  const parent = route.matched.find(r => r.path === '/workspace')
  return (parent?.children || []).filter(c => !c.meta?.hidden).map(c => ({ ...c, fullPath: '/workspace/' + c.path }))
})
const visibleTabs = computed(() => userRole.value === 'admin' ? tabs.value : tabs.value.filter(t => t.meta?.title !== '系统管理'))

function isActive(tab) { return route.path === tab.fullPath }
function navTo(tab) { drawerOpen.value = false; router.push(tab.fullPath) }
function logout() { localStorage.removeItem('csic_token'); localStorage.removeItem('csic_user'); router.push('/') }

const profileVisible = ref(false)
const profileLoading = ref(false)
const profileForm = reactive({ email: '', real_name: '', password: '' })
onMounted(() => { profileForm.email = userInfo.email || ''; profileForm.real_name = userInfo.real_name || '' })

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
    if (profileForm.email) userInfo.email = profileForm.email
    if (profileForm.real_name) userInfo.real_name = profileForm.real_name
    localStorage.setItem('csic_user', JSON.stringify(userInfo))
  } catch (e) { ElMessage.error(e.message || '更新失败') }
  profileLoading.value = false
}

onMounted(() => {
  const s = document.createElement('script')
  s.src = '/js/ocean-particles.js'
  s.onload = () => {
    if (window.OceanParticles && headerEl.value)
      new OceanParticles(headerEl.value, { count: 20, speedMin: 0.12, speedMax: 0.5, opacityMin: 0.06, opacityMax: 0.25, sizeMin: 1, sizeMax: 2.5, flowDirection: 'right', zIndex: 0, colors: ['rgba(34,211,238,{o})', 'rgba(8,145,178,{o})', 'rgba(212,168,67,{o})'] })
  }
  document.head.appendChild(s)
})
</script>

<style scoped>
.vben-layout { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg-page); }

/* Header */
.vben-header { position: relative; height: 58px; flex-shrink: 0; z-index: 100; overflow: hidden; background: linear-gradient(135deg, #050d1a 0%, #0a1628 30%, #0f2347 60%, #1a365d 100%); }
.vben-header::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.25), transparent); }

.bar-inner { position: relative; width: 100%; max-width: 1440px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 58px; z-index: 1; }

/* Brand */
.vben-header-left { display: flex; align-items: center; z-index: 1; margin-right: auto; }
.brand-mark { display: inline-flex; align-items: center; gap: 10px; }
.header-logo-en { height: 26px; filter: brightness(0) invert(1) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)); }
.brand-divider { width: 1px; height: 20px; background: rgba(255, 255, 255, 0.2); }
.brand-text-group { display: flex; align-items: baseline; gap: 6px; }
.brand-text { font-size: 16px; font-weight: 800; color: #fff; letter-spacing: 1px; text-shadow: 0 2px 4px rgba(0,0,0,0.25); }
.brand-sub { font-size: 11px; color: rgba(255,255,255,0.75); font-weight: 500; padding: 2px 8px; background: rgba(34,211,238,0.12); border: 1px solid rgba(34,211,238,0.22); border-radius: 20px; }

/* Right */
.vben-header-right { display: flex; align-items: center; gap: 10px; z-index: 1; }

/* Desktop tabs */
.desktop-tabs { display: flex; align-items: center; gap: 4px; margin-right: 12px; }
.vben-tab { display: inline-flex; align-items: center; gap: 5px; padding: 6px 14px; border-radius: 8px; font-size: 13px; color: rgba(255,255,255,0.75); cursor: pointer; transition: all 0.15s; white-space: nowrap; font-weight: 500; }
.vben-tab:hover { color: #fff; background: rgba(255,255,255,0.1); }
.vben-tab.active { color: #fff; background: #1677ff; box-shadow: 0 2px 8px rgba(22,119,255,0.35); }
.tab-icon { font-size: 15px; }
.tab-title { line-height: 1; }

/* User */
.user-info { display: flex; align-items: center; cursor: pointer; font-size: 13px; padding: 4px 10px; border-radius: 24px; transition: background 0.15s; color: rgba(255,255,255,0.9); }
.user-info:hover { background: rgba(255,255,255,0.08); }
.user-avatar { border: 2px solid rgba(255,255,255,0.15); background: linear-gradient(135deg, #22d3ee 0%, #1677ff 100%) !important; }
.user-name { margin-left: 6px; font-weight: 500; }
.user-arrow { color: rgba(255,255,255,0.45); }

/* Hamburger */
.hamburger-btn { display: none !important; color: #fff !important; }

/* 帮助中心 / 接口文档 快捷入口 */
.header-links { display: flex; align-items: center; gap: 2px; margin-right: 8px; }
.header-link {
  display: flex; align-items: center; gap: 4px; padding: 5px 9px; border-radius: 6px;
  color: rgba(255,255,255,0.85); font-size: 12.5px; text-decoration: none; transition: all .15s;
}
.header-link:hover { color: #fff; background: rgba(255,255,255,0.12); }
@media (max-width: 768px) {
  .header-links { margin-right: 2px; }
  .header-link .link-text { display: none; }
}

/* Content */
.vben-content { flex: 1; padding: 16px 20px 24px; overflow-y: auto; background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); min-height: calc(100vh - 58px); }
.content-inner { max-width: 1440px; margin: 0 auto; }

/* Mobile nav drawer */
.mobile-nav { padding: 12px 0; }
.mobile-nav-title { font-size: 13px; font-weight: 700; color: #64748b; padding: 8px 16px 12px; text-transform: uppercase; letter-spacing: 1px; }
.mobile-nav-item { display: flex; align-items: center; gap: 10px; padding: 12px 16px; font-size: 14px; color: #374151; cursor: pointer; transition: background 0.15s; border-radius: 6px; margin: 2px 8px; }
.mobile-nav-item:hover { background: #f0f5ff; }
.mobile-nav-item.active { background: #e6f0ff; color: #1677ff; font-weight: 600; }

/* ============ RESPONSIVE ============ */
@media (max-width: 900px) {
  .desktop-tabs { display: none !important; }
  .hamburger-btn { display: inline-flex !important; }
  .user-name { display: none; }
  .brand-sub { display: none; }
  .brand-text { font-size: 14px; }
  .bar-inner { padding: 0 12px; }
  .vben-content { padding: 12px 12px 16px; }
}

@media (max-width: 480px) {
  .vben-header { height: 50px; }
  .bar-inner { height: 50px; padding: 0 10px; }
  .header-logo-en { height: 20px; }
  .brand-divider { height: 16px; }
  .brand-text { font-size: 13px; }
  .user-avatar { width: 26px !important; height: 26px !important; }
  .vben-content { padding: 8px 8px 12px; min-height: calc(100vh - 50px); }
}
</style>
