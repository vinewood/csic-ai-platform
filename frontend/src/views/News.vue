<template>
  <div class="news-app">
    <!-- 顶栏 -->
    <div class="news-topbar">
      <div class="topbar-left">
        <h2 class="page-logo">📰 每日资讯</h2>
        <span class="page-sub">AI 智能聚合引擎</span>
      </div>
      <div class="topbar-right">
        <el-date-picker v-model="selectedDate" type="date" placeholder="选择日期" size="small" style="width:150px" @change="loadDigest" />
        <el-input v-model="searchText" placeholder="搜索资讯..." size="small" style="width:200px" clearable :prefix-icon="Search" />
        <el-button type="success" size="small" :icon="MagicStick" :loading="generating" @click="generateDaily">生成今日资讯</el-button>
      </div>
    </div>

    <!-- 统计栏 -->
    <div class="stats-strip">
      <div class="stat-item"><strong>{{ totalArticles }}</strong> 篇资讯</div>
      <div class="stat-item"><strong>{{ digest.length }}</strong> 个分类</div>
      <div class="stat-item"><strong>{{ aiCount }}</strong> 条 AI 摘要</div>
      <div class="stat-item">{{ formatDate }}</div>
    </div>

    <div class="news-layout">
      <!-- 左侧分类筛选 -->
      <aside class="news-sidebar">
        <div class="sidebar-title">分类筛选</div>
        <div class="cat-list">
          <div :class="['cat-item', { active: activeCat === '' }]" @click="activeCat = ''">
            <span class="cat-dot" style="background:#1677ff"></span>
            <span class="cat-name">全部</span>
            <span class="cat-num">{{ totalArticles }}</span>
          </div>
          <div v-for="c in categories" :key="c.name" :class="['cat-item', { active: activeCat === c.name }]" @click="activeCat = c.name">
            <span class="cat-dot" :style="{background: c.color}"></span>
            <span class="cat-name">{{ c.name }}</span>
            <span class="cat-num">{{ c.count }}</span>
          </div>
        </div>

        <div class="sidebar-title" style="margin-top:20px">显示方式</div>
        <div class="view-toggle">
          <el-button :type="viewMode==='card'?'primary':''" size="small" @click="viewMode='card'" :icon="Grid" circle />
          <el-button :type="viewMode==='list'?'primary':''" size="small" @click="viewMode='list'" :icon="List" circle />
        </div>
      </aside>

      <!-- 主内容 -->
      <main class="news-main">
        <!-- 卡片模式 -->
        <div v-if="viewMode==='card'" class="card-grid">
          <div v-for="item in filteredArticles" :key="item.id" class="news-card" @click="openArticle(item)">
            <div class="card-cover" :style="{background: item.gradient}">
              <span class="card-cat-tag">{{ item.category || '综合' }}</span>
              <span v-if="item.summary" class="card-ai-tag">AI 摘要</span>
            </div>
            <div class="card-body">
              <div class="card-meta">
                <span class="card-src">{{ item.source }}</span>
                <span class="card-time">{{ item.time }}</span>
              </div>
              <h4 class="card-title">{{ item.title }}</h4>
              <p v-if="item.summary" class="card-desc">{{ item.summary.slice(0, 100) }}</p>
            </div>
          </div>
        </div>

        <!-- 列表模式 -->
        <div v-else class="list-list">
          <div v-for="(item, i) in filteredArticles" :key="item.id" class="news-row" @click="openArticle(item)">
            <div class="row-num" :style="{background: item.gradient}">{{ i + 1 }}</div>
            <div class="row-body">
              <div class="row-meta">
                <span class="row-src">{{ item.source }}</span>
                <span class="row-time">{{ item.time }}</span>
                <span class="row-cat">{{ item.category }}</span>
              </div>
              <h4 class="row-title">{{ item.title }}</h4>
              <p v-if="item.summary" class="row-desc">{{ item.summary.slice(0, 150) }}</p>
            </div>
            <el-icon class="row-arrow"><ArrowRight /></el-icon>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!filteredArticles.length" class="empty-state">
          <el-icon :size="64" color="#e5e7eb"><Document /></el-icon>
          <p>暂无资讯，点击「生成今日资讯」开始</p>
        </div>
      </main>
    </div>

    <!-- 阅读抽屉 -->
    <el-drawer v-model="readVisible" :title="readArticle?.title" size="560px" destroy-on-close>
      <div class="drawer-content">
        <div class="drawer-meta">
          <el-tag size="small" effect="dark" style="background:#1677ff">{{ readArticle?.source }}</el-tag>
          <span style="color:#94a3b8;font-size:12px;margin-left:8px">{{ readArticle?.time }}</span>
          <el-button size="small" circle style="margin-left:auto" @click="openUrl(readArticle?.url)"><el-icon><Link /></el-icon></el-button>
        </div>
        <div v-if="readArticle?.summary" class="drawer-ai-box">
          <div class="drawer-ai-label">
            <el-icon color="#10b981"><MagicStick /></el-icon>
            <strong>AI 摘要</strong>
          </div>
          <p>{{ readArticle?.summary }}</p>
        </div>
        <el-divider />
        <div class="drawer-placeholder">
          <p>完整文章内容请访问源站查看</p>
          <p style="font-size:12px;color:#bbb">支持 RSS 订阅、邮件推送、PDF 导出等扩展功能</p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiGet, apiPost } from '../api.js'
import { Search, MagicStick, Grid, List, ArrowRight, Document, Link } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const selectedDate = ref(new Date())
const searchText = ref('')
const activeCat = ref('')
const viewMode = ref('card')
const readVisible = ref(false)
const readArticle = ref(null)
const articles = ref([])
const generating = ref(false)

const gradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
  'linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)',
]

const formatDate = computed(() => {
  const d = selectedDate.value || new Date()
  const w = ['日','一','二','三','四','五','六']
  return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} 周${w[d.getDay()]}`
})

const digest = computed(() => {
  const groups = {}
  articles.value.forEach(item => {
    const cat = item.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({
      ...item,
      source: item.url ? extractDomain(item.url) : '来源',
      gradient: gradients[Object.keys(groups).length % gradients.length],
    })
  })
  return Object.entries(groups).map(([category, items]) => ({ category, items }))
})

const categories = computed(() =>
  digest.value.map(d => ({
    name: d.category,
    count: d.items.length,
    color: d.items[0]?.gradient || '#1677ff',
  }))
)

const flatArticles = computed(() =>
  digest.value.flatMap(d => d.items).sort((a, b) => {
    const aiA = a.summary ? 1 : 0, aiB = b.summary ? 1 : 0
    return aiB - aiA
  })
)

const totalArticles = computed(() => flatArticles.value.length)
const aiCount = computed(() => flatArticles.value.filter(a => a.summary).length)

const filteredArticles = computed(() => {
  let list = flatArticles.value
  if (activeCat.value) list = list.filter(a => (a.category || '其他') === activeCat.value)
  if (searchText.value) {
    const kw = searchText.value.toLowerCase()
    list = list.filter(a => a.title.toLowerCase().includes(kw) || a.summary?.toLowerCase().includes(kw))
  }
  return list
})

function extractDomain(url) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return '来源' }
}

onMounted(() => loadDigest())

async function generateDaily() {
  generating.value = true
  try {
    const res = await apiPost('/api/rss/generate-daily')
    if (res?.digest) {
      ElMessage.success(res.message || '今日资讯已生成')
      await loadDigest()
      try {
        await ElMessageBox.confirm('DeepSeek 已优化生成今日资讯。是否推送给已订阅邮箱？', '推送确认', {
          confirmButtonText: '推送', cancelButtonText: '暂不', type: 'info'
        })
        ElMessage.success('已加入推送队列')
      } catch { ElMessage.info('未推送') }
    } else {
      ElMessage.info(res?.message || '暂无新资讯')
    }
  } catch (e) { ElMessage.error('生成失败') }
  generating.value = false
}

async function loadDigest() {
  try {
    const params = {}
    if (selectedDate.value) params.date = selectedDate.value.toISOString().split('T')[0]
    const res = await apiGet('/api/rss/articles', { params })
    const arr = res?.articles || res
    articles.value = Array.isArray(arr) ? arr : []
  } catch {
    articles.value = []
  }
}

function openArticle(item) {
  readArticle.value = { ...item, source: item.source || extractDomain(item.url) }
  readVisible.value = true
}

function openUrl(url) {
  if (url) window.open(url)
}
</script>

<style scoped>
.news-app { padding: 0; min-height: 100vh; background: #f5f6fa; }

/* 顶栏 */
.news-topbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; padding: 14px 24px; border-bottom: 1px solid #e8ebf0;
  position: sticky; top: 0; z-index: 10;
}
.topbar-left { display: flex; align-items: baseline; gap: 10px; }
.page-logo { margin: 0; font-size: 18px; font-weight: 700; color: #1a1a2e; }
.page-sub { font-size: 12px; color: #94a3b8; }
.topbar-right { display: flex; align-items: center; gap: 10px; }

/* 统计条 */
.stats-strip {
  display: flex; gap: 32px; padding: 12px 24px;
  background: #fff; border-bottom: 1px solid #f0f0f0;
}
.stat-item { font-size: 13px; color: #64748b; }
.stat-item strong { color: #1677ff; margin-right: 4px; }

/* 布局 */
.news-layout { display: flex; gap: 0; max-width: 1400px; margin: 0 auto; }

/* 侧边栏 */
.news-sidebar {
  width: 200px; min-width: 200px; padding: 20px 16px;
  background: #fff; border-right: 1px solid #e8ebf0; min-height: calc(100vh - 120px);
}
.sidebar-title { font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; }
.cat-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 8px; cursor: pointer; margin-bottom: 3px;
  transition: all 0.15s;
}
.cat-item:hover { background: #f0f5ff; }
.cat-item.active { background: #e6f0ff; font-weight: 600; }
.cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cat-name { flex: 1; font-size: 13px; color: #374151; }
.cat-num { font-size: 11px; color: #94a3b8; }
.view-toggle { display: flex; gap: 6px; }

/* 主内容 */
.news-main { flex: 1; padding: 20px 24px; overflow-y: auto; min-width: 0; }

/* 卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.news-card {
  background: #fff; border-radius: 12px; overflow: hidden;
  border: 1px solid #e5e7eb; cursor: pointer;
  transition: all 0.2s;
}
.news-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.08); }
.card-cover {
  height: 100px; display: flex; align-items: flex-end; justify-content: space-between;
  padding: 12px; position: relative;
}
.card-cat-tag {
  background: rgba(255,255,255,0.9); color: #1a1a2e; font-size: 11px;
  font-weight: 600; padding: 3px 10px; border-radius: 20px;
}
.card-ai-tag { background: #10b981; color: #fff; font-size: 10px; padding: 3px 8px; border-radius: 20px; }
.card-body { padding: 14px; }
.card-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.card-src { font-size: 12px; color: #1677ff; font-weight: 500; }
.card-time { font-size: 11px; color: #94a3b8; }
.card-title { margin: 0 0 6px; font-size: 14px; font-weight: 600; color: #1a1a2e; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-desc { font-size: 12px; color: #6b7280; line-height: 1.6; margin: 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

/* 列表模式 */
.list-list { display: flex; flex-direction: column; gap: 6px; }
.news-row {
  display: flex; align-items: center; gap: 16px;
  background: #fff; border: 1px solid #eee; border-radius: 10px;
  padding: 16px 20px; cursor: pointer; transition: all 0.15s;
}
.news-row:hover { border-color: #bae0ff; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.row-num {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px; font-weight: 700; flex-shrink: 0;
}
.row-body { flex: 1; min-width: 0; }
.row-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.row-src { font-size: 12px; color: #1677ff; font-weight: 500; }
.row-time { font-size: 11px; color: #94a3b8; }
.row-cat { font-size: 11px; color: #fff; background: #1677ff; padding: 1px 8px; border-radius: 10px; }
.row-title { margin: 0 0 3px; font-size: 15px; font-weight: 600; color: #1a1a2e; }
.row-desc { font-size: 13px; color: #6b7280; margin: 0; }
.row-arrow { color: #d1d5db; flex-shrink: 0; }

.empty-state { text-align: center; padding: 100px 0; color: #bbb; }
.empty-state p { margin-top: 12px; font-size: 14px; }

/* 抽屉 */
.drawer-content { padding: 0 4px; }
.drawer-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.drawer-ai-box {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-radius: 10px; padding: 16px; border: 1px solid #a7f3d0;
}
.drawer-ai-label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #065f46; margin-bottom: 8px; }
.drawer-ai-box p { font-size: 14px; line-height: 1.8; color: #374151; margin: 0; }
.drawer-placeholder { text-align: center; padding: 40px 0; color: #94a3b8; font-size: 13px; }
</style>
