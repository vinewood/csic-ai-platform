<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1504711434969-e338861683be?w=1200&q=80);">
      <div class="hero-content">
        <h2>每日资讯</h2>
        <p>AI 智能整理 · 分类聚合 · 一键订阅</p>
      </div>
    </div>

    <!-- 日期导航 -->
    <div class="news-toolbar">
      <el-date-picker v-model="selectedDate" type="date" placeholder="选择日期" style="width:150px;" @change="loadDigest" />
      <span class="toolbar-hint">每日 AI 自动整理最新资讯，共 {{ totalArticles }} 篇</span>
      <el-button size="small" type="primary" round :icon="Plus" style="margin-left:auto;">订阅推送</el-button>
    </div>

    <!-- 日报封面 -->
    <div class="daily-cover">
      <div class="cover-left">
        <div class="cover-date">{{ formatDate }}</div>
        <div class="cover-title">资讯简报</div>
        <div class="cover-desc">AI 智能聚合 · {{ digest.length }} 个分类 · {{ totalArticles }} 条资讯</div>
      </div>
      <div class="cover-right">
        <div class="cover-stat" v-for="s in coverStats" :key="s.label">
          <div class="cover-stat-val">{{ s.value }}</div>
          <div class="cover-stat-lbl">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 分类资讯 -->
    <div v-for="sec in digest" :key="sec.category" class="news-section">
      <div class="section-head">
        <div class="section-title">
          <el-tag :type="sec.tagType" effect="dark" size="default" class="section-tag">{{ sec.category }}</el-tag>
          <span class="section-count">{{ sec.items.length }} 篇</span>
        </div>
        <el-button v-if="sec.items.length > 3" text size="small" type="primary">查看全部 →</el-button>
      </div>

      <div class="article-list">
        <div v-for="(item, i) in sec.items" :key="i" class="article-item" @click="openArticle(item)">
          <div class="article-badge" :style="{background: sec.tagColor}">{{ i + 1 }}</div>
          <div class="article-body">
            <div class="article-header-line">
              <span class="article-src">{{ item.source }}</span>
              <span class="article-dot">·</span>
              <span class="article-time">{{ item.time }}</span>
              <el-tag v-if="item.aiSummary" size="small" type="success" effect="light" class="ai-badge">AI</el-tag>
            </div>
            <h4 class="article-title">{{ item.title }}</h4>
            <p v-if="item.aiSummary" class="article-ai-summary">{{ item.aiSummary }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 无数据 -->
    <div v-if="!digest.length" class="empty-news">
      <el-icon :size="48" color="#d1d5db"><Connection /></el-icon>
      <p>暂无资讯数据</p>
    </div>

    <!-- 阅读弹窗 -->
    <el-dialog v-model="readVisible" :title="readArticle?.title" width="640px" destroy-on-close>
      <div class="read-dialog">
        <div class="read-meta-bar">
          <el-tag size="small">{{ readArticle?.source }}</el-tag>
          <span style="color:#94a3b8;font-size:12px;margin-left:8px;">{{ readArticle?.time }}</span>
        </div>
        <div v-if="readArticle?.aiSummary" class="read-ai-box">
          <el-icon color="#10b981" style="margin-right:6px;"><Promotion /></el-icon>
          <strong>AI摘要：</strong>{{ readArticle?.aiSummary }}
        </div>
        <el-divider />
        <p class="read-placeholder">完整文章内容需从源站获取。在实际系统中将展示 RSS 拉取的全文内容。</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiGet, apiPost } from '../api.js'
import { Plus, Promotion, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const selectedDate = ref(new Date())
const readVisible = ref(false)
const readArticle = ref(null)
const articles = ref([])

const formatDate = computed(() => {
  const d = selectedDate.value || new Date()
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 周${weekdays[d.getDay()]}`
})

const tagConfig = {
  '官方要闻': { tagType: 'danger', tagColor: '#dc2626' },
  '党建动态': { tagType: 'warning', tagColor: '#d97706' },
  '船舶制造': { tagType: 'primary', tagColor: '#2563eb' },
  '科技前沿': { tagType: 'success', tagColor: '#16a34a' },
  '全球经济': { tagType: 'info', tagColor: '#0891b2' }
}

const digest = computed(() => {
  const groups = {}
  articles.value.forEach(item => {
    const cat = item.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({
      ...item,
      source: item.url ? extractDomain(item.url) : '来源',
      aiSummary: item.summary || ''
    })
  })
  return Object.entries(groups).map(([category, items]) => {
    const cfg = tagConfig[category] || { tagType: 'info', tagColor: '#6b7280' }
    return { category, tagType: cfg.tagType, tagColor: cfg.tagColor, items }
  })
})

const totalArticles = computed(() => digest.value.reduce((s, sec) => s + sec.items.length, 0))
const coverStats = computed(() => [
  { label: '分类', value: digest.value.length },
  { label: '资讯', value: totalArticles.value },
  { label: 'AI摘要', value: digest.value.reduce((s, sec) => s + sec.items.filter(i => i.aiSummary).length, 0) },
  { label: '来源', value: new Set(digest.value.flatMap(s => s.items.map(i => i.source))).size }
])

function extractDomain(url) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return '来源' }
}

onMounted(() => { loadDigest() })

async function loadDigest() {
  try {
    const params = {}
    if (selectedDate.value) {
      params.date = selectedDate.value.toISOString().split('T')[0]
    }
    const res = await apiGet('/api/rss/articles', { params })
    articles.value = (res && res.articles) ? res.articles : (Array.isArray(res) ? res : [])
  } catch (e) {
    ElMessage.error('加载资讯失败: ' + (e.message || '未知错误'))
    articles.value = []
  }
}

function openArticle(item) {
  readArticle.value = {
    id: item.id,
    title: item.title,
    source: item.source || extractDomain(item.url),
    time: item.time,
    aiSummary: item.summary || ''
  }
  readVisible.value = true
}
</script>

<style scoped>
/* 工具栏 */
.news-toolbar {
  display: flex; align-items: center; gap: 12px;
  background: #fff; padding: 14px 18px; border-radius: 10px;
  border: 1px solid #e5e7eb; margin-bottom: 16px;
}
.toolbar-hint { font-size: 13px; color: #94a3b8; }

/* 日报封面 */
.daily-cover {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #0f2347 0%, #1a365d 100%);
  border-radius: 12px; padding: 28px 32px; margin-bottom: 20px;
  color: #fff;
}
.cover-date { font-size: 14px; opacity: 0.7; margin-bottom: 4px; }
.cover-title { font-size: 28px; font-weight: 800; letter-spacing: 1px; }
.cover-desc { font-size: 13px; opacity: 0.6; margin-top: 6px; }
.cover-right { display: flex; gap: 28px; }
.cover-stat { text-align: center; }
.cover-stat-val { font-size: 26px; font-weight: 700; }
.cover-stat-lbl { font-size: 11px; opacity: 0.6; margin-top: 2px; }

/* 分类 */
.news-section { margin-bottom: 18px; }
.section-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.section-title { display: flex; align-items: center; gap: 8px; }
.section-tag { font-size: 13px; padding: 5px 14px; border-radius: 20px; }
.section-count { font-size: 12px; color: #94a3b8; }

/* 文章列表 */
.article-list { display: flex; flex-direction: column; gap: 8px; }
.article-item {
  display: flex; gap: 14px; align-items: flex-start;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 14px 18px; cursor: pointer;
  transition: all 0.15s;
}
.article-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); border-color: #bae0ff; }
.article-badge {
  width: 28px; height: 28px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 12px; font-weight: 700; flex-shrink: 0;
  margin-top: 2px;
}
.article-body { flex: 1; min-width: 0; }
.article-header-line { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }
.article-src { font-size: 12px; color: #1677ff; font-weight: 500; }
.article-dot { color: #d1d5db; font-size: 10px; }
.article-time { font-size: 11px; color: #94a3b8; }
.ai-badge { font-size: 10px; padding: 0 6px; height: 18px; line-height: 18px; }
.article-title {
  margin: 0 0 6px; font-size: 14px; font-weight: 600; color: #1a1a2e; line-height: 1.5;
}
.article-title:hover { color: #1677ff; }
.article-ai-summary {
  font-size: 13px; color: #4b5563; line-height: 1.7; margin: 0;
  padding: 8px 12px; background: #f0fdf4; border-radius: 6px;
  border-left: 3px solid #10b981;
}

.empty-news { text-align: center; padding: 80px 0; color: #94a3b8; }
.empty-news p { margin-top: 10px; }

/* 阅读弹窗 */
.read-dialog { line-height: 1.8; }
.read-meta-bar { margin-bottom: 14px; }
.read-ai-box {
  background: #f0fdf4; padding: 12px 16px; border-radius: 8px;
  border-left: 3px solid #10b981; font-size: 14px; line-height: 1.7;
  display: flex; align-items: flex-start;
}
.read-placeholder { color: #94a3b8; line-height: 1.8; }
</style>
