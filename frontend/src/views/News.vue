<template>
  <div class="news-app">
    <!-- 顶栏 -->
    <div class="news-topbar">
      <div class="topbar-left">
        <h2 class="page-logo">📰 每日资讯</h2>
        <span class="page-sub">{{ formatDate }}</span>
      </div>
      <div class="topbar-right">
        <el-date-picker v-model="selectedDate" type="date" placeholder="选择日期" size="small" style="width:140px" @change="loadDigest" format="YYYY/MM/DD" value-format="YYYY-MM-DD" />
        <el-button size="small" @click="goToday">今天</el-button>
        <el-input v-model="searchText" placeholder="搜索..." size="small" style="width:150px" clearable :prefix-icon="Search" />
        <el-button type="success" size="small" :icon="MagicStick" :loading="generating" @click="generateDaily">生成</el-button>
      </div>
    </div>

    <div class="news-layout">
      <!-- 左侧分类 -->
      <aside class="news-sidebar">
        <div class="sidebar-title">分类</div>
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
      </aside>

      <!-- 瀑布流 -->
      <main class="news-main">
        <div v-if="!filteredArticles.length" class="empty-state">
          <el-icon :size="48" color="#e5e7eb"><Document /></el-icon>
          <p>暂无资讯，点击「生成」获取今日资讯</p>
        </div>

        <div class="masonry" v-else>
          <div v-for="item in filteredArticles" :key="item.id" class="masonry-card" @click="openArticle(item)">
            <div class="card-info">
              <div class="card-meta">
                <span class="card-src">{{ item.source }}</span>
                <span class="card-time">{{ item.time }}</span>
                <span class="card-cat" :style="{background: item.gradient}">{{ item.category || '综合' }}</span>
                <span v-if="item.summary" class="card-ai">AI</span>
              </div>
              <h4 class="card-title">{{ cleanHtml(item.title) }}</h4>
              <p v-if="item.summary" class="card-desc">{{ cleanHtml(item.summary).slice(0, 120) }}</p>
            </div>
          </div>
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
          <p v-html="cleanHtml(readArticle?.summary || '')"></p>
        </div>
        <el-divider />
        <div class="drawer-placeholder">
          <p>完整文章请访问源站查看</p>
          <p style="font-size:12px;color:#bbb">支持 RSS 订阅、邮件推送等扩展功能</p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiGet, apiPost } from '../api.js'
import { Search, MagicStick, Document, Link } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const selectedDate = ref(new Date())
const searchText = ref('')
const activeCat = ref('')
const readVisible = ref(false)
const readArticle = ref(null)
const articles = ref([])
const generating = ref(false)

const gradients = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
  'linear-gradient(135deg, #a18cd1, #fbc2eb)',
  'linear-gradient(135deg, #fccb90, #d57eeb)',
  'linear-gradient(135deg, #2193b0, #6dd5ed)',
]

const formatDate = computed(() => {
  const d = selectedDate.value
  if (typeof d === 'string') return d
  const w = ['日','一','二','三','四','五','六']
  return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} 周${w[d.getDay()]}`
})

const digest = computed(() => {
  const groups = {}
  articles.value.forEach(item => {
    const cat = item.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({ ...item, source: item.url ? extractDomain(item.url) : '来源', gradient: gradients[Object.keys(groups).length % gradients.length] })
  })
  return Object.entries(groups).map(([category, items]) => ({ category, items }))
})

const categories = computed(() => digest.value.map(d => ({ name: d.category, count: d.items.length, color: d.items[0]?.gradient || '#1677ff' })))
const flatArticles = computed(() => digest.value.flatMap(d => d.items).sort((a,b) => (b.summary ? 1 : 0) - (a.summary ? 1 : 0)))
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

function extractDomain(url) { try { return new URL(url).hostname.replace(/^www\./, '') } catch { return '来源' } }

function cleanHtml(text) {
  if (!text) return ''
  let t = String(text)
  // Replace break tags and paragraph closings with newlines
  t = t.replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>/gi, '\n\n').replace(/<\/div>/gi, '\n')
  // Remove ALL remaining HTML tags
  t = t.replace(/<[^>]*>/g, '')
  // Decode HTML entities
  t = t.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  t = t.replace(/&quot;/g, '"').replace(/&#39;/g, "'")
  t = t.replace(/&nbsp;/g, ' ').replace(/&#?\w+;/g, ' ')
  // Collapse whitespace
  t = t.replace(/\s+/g, ' ').replace(/\n\s*\n/g, '\n').trim()
  return t
}

onMounted(() => loadDigest())

function goToday() {
  selectedDate.value = new Date()
  loadDigest()
}

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
    } else { ElMessage.info(res?.message || '暂无新资讯') }
  } catch { ElMessage.error('生成失败') }
  generating.value = false
}

async function loadDigest() {
  try {
    const params = {}
    if (selectedDate.value) {
      const d = selectedDate.value
      params.date = typeof d === 'string' ? d : d.toISOString().split('T')[0]
    }
    // apiGet(path) 只接收一个参数，日期筛选需手动拼 query string，否则参数不会发出
    const qs = params.date ? `?date=${encodeURIComponent(params.date)}` : ''
    const res = await apiGet('/api/rss/articles' + qs)
    articles.value = Array.isArray(res?.articles) ? res.articles : (Array.isArray(res) ? res : [])
  } catch { articles.value = [] }
}

function openArticle(item) { readArticle.value = item; readVisible.value = true }
function openUrl(url) { if (url) window.open(url) }
</script>

<style scoped>
.news-app { padding: 0; min-height: 100vh; background: #f5f6fa; }

.news-topbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; padding: 10px 20px; border-bottom: 1px solid #e8ebf0;
  position: sticky; top: 0; z-index: 10;
}
.topbar-left { display: flex; align-items: baseline; gap: 10px; }
.page-logo { margin: 0; font-size: 17px; font-weight: 700; color: #1a1a2e; }
.page-sub { font-size: 12px; color: #94a3b8; }
.topbar-right { display: flex; align-items: center; gap: 10px; }

.news-layout { display: flex; max-width: 1200px; margin: 0 auto; }

.news-sidebar {
  width: 180px; min-width: 180px; padding: 16px; background: #fff;
  border-right: 1px solid #e8ebf0; min-height: calc(100vh - 56px);
}
.sidebar-title { font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
.cat-item { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-radius: 6px; cursor: pointer; margin-bottom: 2px; }
.cat-item:hover { background: #f0f5ff; }
.cat-item.active { background: #e6f0ff; font-weight: 600; }
.cat-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.cat-name { flex: 1; font-size: 13px; color: #374151; }
.cat-num { font-size: 11px; color: #94a3b8; }

.news-main { flex: 1; padding: 16px 20px; min-width: 0; }

/* 瀑布流 */
.masonry { column-count: 3; column-gap: 14px; }
.masonry-card {
  break-inside: avoid; background: #fff; border-radius: 10px;
  overflow: hidden; cursor: pointer; margin-bottom: 12px;
  border: 1px solid #eee; transition: all 0.2s;
}
.masonry-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
.card-info { padding: 14px 16px; }
.card-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
.card-src { font-size: 11px; color: #1677ff; font-weight:500; }
.card-time { font-size: 10px; color: #94a3b8; }
.card-cat { font-size: 10px; color: #fff; padding: 1px 8px; border-radius: 10px; }
.card-ai { background: #10b981; color: #fff; font-size: 10px; padding: 1px 6px; border-radius: 10px; }
.card-title { margin: 0 0 4px; font-size: 14px; font-weight:600; color: #1a1a2e; line-height:1.5; word-break:break-word; }
.card-desc { font-size: 12px; color: #6b7280; line-height:1.6; margin:0; word-break:break-word; }

.empty-state { text-align: center; padding: 80px 0; color: #bbb; }
.empty-state p { margin-top: 8px; font-size: 14px; }

@media (max-width: 900px) { .masonry { column-count: 2; } }
@media (max-width: 600px) {
  .masonry { column-count: 1; }
  .news-sidebar { display: none; }
  .news-main { padding: 10px; }
  .news-topbar { flex-wrap: wrap; gap: 6px; padding: 8px 10px; }
  .topbar-right { width: 100%; flex-wrap: wrap; }
  .topbar-right .el-input { flex: 1; min-width: 0; }
  .topbar-right .el-button { flex-shrink: 0; }
}

.drawer-content { padding: 0 4px; }
.drawer-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.drawer-ai-box {
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  border-radius: 10px; padding: 16px; border: 1px solid #a7f3d0;
}
.drawer-ai-label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #065f46; margin-bottom: 8px; }
.drawer-ai-box p { font-size: 14px; line-height: 1.8; color: #374151; margin: 0; }
.drawer-placeholder { text-align: center; padding: 40px 0; color: #94a3b8; font-size: 13px; }
</style>
