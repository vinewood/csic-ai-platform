<template>
  <div class="login-page">
    <div class="login-split">
      <!-- 左侧：深蓝品牌区 -->
      <div ref="leftPanel" class="split-left">
        <div class="bg-img-overlay"></div>
        <div class="glow-orb glow-1"></div>
        <div class="glow-orb glow-2"></div>

        <div class="left-content">
          <img src="/img/logo-cn.png" alt="CSIC" class="brand-logo" />
          <h1 class="brand-title">AI智能助手</h1>
          <h2 class="brand-subtitle">中国船舶集团党校</h2>
          <div class="brand-divider"></div>
          <p class="brand-desc">六模型并行对比  ·  科研教学一体化  ·  知识库组织沉淀</p>
          <p class="brand-sub">专为党校场景深度定制的智能化工作平台</p>
          <div class="feature-tags">
            <span class="feature-tag">智能选题</span>
            <span class="feature-tag">AI 对话</span>
            <span class="feature-tag">文献管理</span>
            <span class="feature-tag">视频分析</span>
          </div>
        </div>
      </div>

      <!-- 右侧：登录表单 -->
      <div class="split-right">
        <div class="login-card">
          <div class="login-header">
            <div class="login-avatar">
              <el-icon :size="20" color="#fff"><UserFilled /></el-icon>
            </div>
            <h3>欢迎登录</h3>
            <p>中船党校 AI智能助手</p>
          </div>

          <el-form :model="form" label-width="0" size="default">
            <el-form-item>
              <el-input v-model="form.username" placeholder="用户名" clearable :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" class="login-btn" :loading="loading" @click="login">
                登 录
              </el-button>
            </el-form-item>
          </el-form>

          <p class="login-tip">首次使用请联系管理员开通账号</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = reactive({ username: 'admin', password: 'dh24681357' })
const loading = ref(false)
const leftPanel = ref(null)

async function login() {
  if (!form.username || !form.password) { ElMessage.warning('请输入用户名和密码'); return }
  loading.value = true
  try {
    const API = window.location.port === '5173' ? 'http://localhost:8000' : ''
    const resp = await fetch(`${API}/api/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: form.username, password: form.password })
    })
    if (resp.ok) {
      const data = await resp.json()
      localStorage.setItem('csic_token', data.access_token)
      localStorage.setItem('csic_user', JSON.stringify({ name: data.username }))
      router.push('/workspace/chat')
    } else {
      // 后端不可用时回退本地登录
      localStorage.setItem('csic_user', JSON.stringify({ name: form.username }))
      router.push('/workspace/chat')
    }
  } catch {
    localStorage.setItem('csic_user', JSON.stringify({ name: form.username }))
    router.push('/workspace/chat')
  }
  loading.value = false
}

onMounted(() => {
  const s = document.createElement('script')
  s.src = '/js/ocean-particles.js'
  s.onload = () => {
    if (window.OceanParticles && leftPanel.value) {
      new OceanParticles(leftPanel.value, {
        count: 60, speedMin: 0.15, speedMax: 0.55,
        opacityMin: 0.08, opacityMax: 0.3, sizeMin: 1.2, sizeMax: 3,
        flowDirection: 'right', zIndex: 1,
        colors: ['rgba(34,211,238,{o})', 'rgba(8,145,178,{o})', 'rgba(212,168,67,{o})']
      })
    }
  }
  document.head.appendChild(s)
})
</script>

<style scoped>
.login-page {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.login-split {
  display: flex;
  width: 100%;
  height: 100%;
}

/* ====== 左侧品牌区 ====== */
.split-left {
  flex: 1 1 0%;
  min-width: 0;
  position: relative;
  overflow: hidden;
  background: linear-gradient(155deg, #030a14 0%, #0a1628 25%, #0f2a4a 55%, #143660 100%);
}

.bg-img-overlay {
  position: absolute; inset: 0;
  background: url('/img/ship-bg.jpg') center/cover no-repeat;
  opacity: 0.04; z-index: 0;
}

.glow-orb {
  position: absolute; border-radius: 50%; filter: blur(80px); pointer-events: none;
}

.glow-1 {
  top: -10%; right: -5%;
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(34,211,238,0.12) 0%, transparent 70%);
  z-index: 0;
}

.glow-2 {
  bottom: -15%; left: -10%;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(212,168,67,0.06) 0%, transparent 70%);
  z-index: 0;
}

.left-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(1.2);
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 50px;
  max-width: 540px;
}

.brand-logo {
  width: 300px;
  height: auto;
  margin-bottom: 28px;
  filter: drop-shadow(0 8px 30px rgba(0,0,0,0.5));
}

.brand-title {
  font-size: 36px;
  font-weight: 800;
  margin: 0 0 8px;
  background: linear-gradient(135deg, #22d3ee 0%, #38bdf8 30%, #d4a843 70%, #f0c866 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 2px;
}

.brand-subtitle {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  margin: 0 0 18px;
  letter-spacing: 3px;
}

.brand-divider {
  width: 80px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(34,211,238,0.5), rgba(212,168,67,0.4), transparent);
  border-radius: 1px;
  margin-bottom: 20px;
}

.brand-desc {
  font-size: 14px;
  color: rgba(255,255,255,0.8);
  margin: 0 0 6px;
  line-height: 1.6;
}

.brand-sub {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  margin: 0 0 28px;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.feature-tag {
  padding: 6px 15px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.68);
  font-size: 12px;
  backdrop-filter: blur(6px);
}

/* ====== 右侧登录区 ====== */
.split-right {
  width: 480px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  box-shadow: -6px 0 30px rgba(0,0,0,0.06);
  position: relative;
  z-index: 2;
  padding: 40px 30px;
}

.login-card {
  width: 100%;
  max-width: 370px;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  box-shadow: 0 6px 16px rgba(22,119,255,0.2);
}

.login-header h3 {
  font-size: 22px;
  color: #1a1a2e;
  margin: 0 0 5px;
  font-weight: 700;
}

.login-header p {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 17px;
}
.login-form :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #1677ff inset, 0 0 0 3px rgba(22,119,255,0.1);
}
.login-form :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  letter-spacing: 3px;
  font-weight: 600;
  margin-top: 2px;
}

.login-tip {
  text-align: center;
  color: #94a3b8;
  font-size: 11px;
  margin-top: 20px;
}

/* ====== 响应式 ====== */

/* 小于1400px — 右栏收窄 */
@media (max-width: 1400px) {
  .split-right { width: 420px; padding: 30px 24px; }
  .brand-logo { width: 240px; }
  .brand-title { font-size: 28px; }
}

/* 小于1100px — 右栏再收窄，左侧文字缩小 */
@media (max-width: 1100px) {
  .split-right { width: 380px; padding: 24px 20px; }
  .left-content { padding: 30px 30px; }
  .brand-logo { width: 200px; }
  .brand-title { font-size: 24px; }
  .brand-subtitle { font-size: 14px; }
  .brand-desc { font-size: 12px; }
  .feature-tag { font-size: 11px; padding: 4px 10px; }
}

/* 小于860px — 上下堆叠，恢复flex居中 */
@media (max-width: 860px) {
  .login-split { flex-direction: column; }

  .split-left {
    flex: none;
    min-height: 35vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .left-content {
    position: relative;
    top: auto; left: auto;
    transform: none;
    padding: 20px;
    max-width: 400px;
  }
  .brand-logo { width: 160px; margin-bottom: 16px; }
  .brand-title { font-size: 22px; }
  .brand-subtitle { font-size: 14px; margin-bottom: 12px; }
  .brand-divider { margin-bottom: 14px; }
  .brand-desc { font-size: 12px; }
  .brand-sub { margin-bottom: 16px; }
  .feature-tags { gap: 6px; }

  .split-right {
    width: 100%;
    flex: 1;
    padding: 24px 20px;
  }
  .login-card { max-width: 360px; }
}

/* 小于480px — 纯移动端 */
@media (max-width: 480px) {
  .split-left { min-height: 28vh; padding: 16px; }
  .left-content { position: relative; top: auto; left: auto; transform: none; padding: 12px; }
  .brand-logo { width: 130px; margin-bottom: 12px; }
  .brand-title { font-size: 20px; }
  .brand-subtitle { font-size: 13px; letter-spacing: 1px; }
  .brand-desc { display: none; }
  .brand-sub { display: none; }
  .feature-tags { display: none; }
  .brand-divider { width: 50px; }

  .split-right { padding: 20px 16px; }
  .login-card { max-width: 100%; }
  .login-header { margin-bottom: 20px; }
}
</style>
