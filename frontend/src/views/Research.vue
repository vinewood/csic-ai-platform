<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1532619675605-1ede6c2ed2b0?w=1200&q=80);">
      <div class="hero-content">
        <h2>科研工作台</h2>
        <p>智能选题 · 选题测评 · 文献检索 · 项目空间</p>
      </div>
    </div>

    <el-card shadow="never" class="research-card">
      <el-tabs v-model="tab" class="research-tabs">

        <!-- ====== 智能选题 ====== -->
        <el-tab-pane label="智能选题" name="topics">
          <!-- AI 辅助选题 -->
          <div class="topic-generator">
            <h3>AI 智能选题生成</h3>
            <p>输入研究方向或关键词，AI 为您推荐规范的学术选题</p>
            <el-input
              v-model="topicInput"
              type="textarea"
              :rows="3"
              placeholder="请输入您的研究方向、兴趣领域或关键词，如：基层党建与数字化转型、船舶工业高质量发展..."
            />
            <div class="topic-actions">
              <el-button type="primary" :icon="Lightning" @click="generateTopics">生成选题</el-button>
              <el-button :icon="Refresh" @click="topicInput = ''">清空</el-button>
            </div>
          </div>

          <!-- 选题结果 -->
          <div v-if="generatedTopics.length" class="topic-results">
            <h4>推荐选题（{{ generatedTopics.length }} 个）</h4>
            <div v-for="(t, i) in generatedTopics" :key="i" class="topic-item">
              <div class="topic-num">{{ i + 1 }}</div>
              <div class="topic-body">
                <div class="topic-name">{{ t.name }}</div>
                <div class="topic-desc">{{ t.desc }}</div>
                <div class="topic-tags">
                  <el-tag size="small" effect="light" type="primary">{{ t.field }}</el-tag>
                  <el-tag size="small" effect="light" type="success">可行性 {{ t.feasibility }}</el-tag>
                  <el-tag size="small" effect="light" type="warning">创新性 {{ t.innovation }}</el-tag>
                </div>
                <div class="topic-ops">
                  <el-button link type="primary" size="small" :icon="EditPen" @click="useTopic(t)">采用选题</el-button>
                  <el-button link type="primary" size="small" :icon="DataAnalysis" @click="evalTopic(t)">深度测评</el-button>
                  <el-button link size="small" :icon="Share" @click="ElMessage.success('已复制')">分享</el-button>
                </div>
              </div>
            </div>
          </div>

          <el-divider />

          <!-- 期刊选题方向 -->
          <div class="journal-section">
            <div class="section-hd">
              <h4>期刊重点选题方向</h4>
              <el-button text type="primary" size="small">查看更多 →</el-button>
            </div>
            <el-row :gutter="12">
              <el-col :span="8" :xs="24" v-for="j in journals" :key="j.id" style="margin-bottom:10px;">
                <el-card shadow="hover" class="journal-card">
                  <div class="journal-name">{{ j.name }}</div>
                  <div class="journal-year">{{ j.year }} · {{ j.issue }}</div>
                  <div class="journal-topic">「{{ j.topic }}」</div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- ====== 选题测评 ====== -->
        <el-tab-pane label="选题测评" name="evaluate">
          <div class="eval-section">
            <h3>选题测评</h3>
            <p>输入您的选题名称，AI 从多个维度进行综合评估</p>
            <el-input v-model="evalTopicTitle" placeholder="请输入您的选题名称，如：新时代基层党建引领乡村治理现代化的路径研究" />
            <el-button type="primary" :icon="DataAnalysis" @click="doEvaluate" style="margin-top:12px;">开始测评</el-button>

            <div v-if="evalResult" class="eval-result">
              <el-row :gutter="16">
                <el-col :span="6" :xs="12" v-for="d in evalResult.dimensions" :key="d.name">
                  <el-card shadow="never" class="eval-dim">
                    <div class="dim-score" :style="{color: d.color}">{{ d.score }}</div>
                    <div class="dim-name">{{ d.name }}</div>
                    <el-progress :percentage="d.score" :stroke-width="6" :color="d.color" :show-text="false" />
                  </el-card>
                </el-col>
              </el-row>
              <el-card shadow="never" class="eval-advice">
                <template #header><span style="font-weight:600;">综合建议</span></template>
                <p>{{ evalResult.advice }}</p>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <!-- ====== 文献检索 ====== -->
        <el-tab-pane label="文献检索" name="literature">
          <div class="section-intro">
            <h3>学术文献检索</h3>
            <p>聚合维普、AMiner 等学术数据源，支持关键词、作者、机构检索</p>
          </div>
          <div class="lit-search-bar">
            <el-input v-model="litQuery" placeholder="输入关键词、论文标题、作者姓名..." style="flex:1;" clearable />
            <el-select v-model="litSource" style="width:140px;">
              <el-option label="全部来源" value="all" />
              <el-option label="维普" value="vip" />
              <el-option label="AMiner" value="aminer" />
            </el-select>
            <el-select v-model="litField" style="width:120px;">
              <el-option label="关键词" value="keyword" />
              <el-option label="标题" value="title" />
              <el-option label="作者" value="author" />
              <el-option label="机构" value="institution" />
            </el-select>
            <el-button type="primary" :icon="Search" @click="searchLiterature">检索</el-button>
          </div>

          <div v-if="litResults.length" class="lit-results">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
              <span style="font-size:13px;color:#4b5563;">共 {{ litResults.length }} 条结果</span>
              <el-button text size="small" :icon="Download">导出引文</el-button>
            </div>
            <div v-for="(r, i) in litResults" :key="i" class="lit-item">
              <div class="lit-num">{{ i + 1 }}</div>
              <div class="lit-body">
                <div class="lit-title">{{ r.title }}</div>
                <div class="lit-authors">{{ r.authors }}</div>
                <div class="lit-meta">{{ r.journal }} · {{ r.year }} · {{ r.citations }} 引用</div>
                <div class="lit-abstract">{{ r.abstract }}</div>
                <div class="lit-ops">
                  <el-button link type="primary" size="small" :icon="Reading">查看</el-button>
                  <el-button link size="small" :icon="Star">收藏</el-button>
                  <el-button link size="small" :icon="Share">引用</el-button>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="litSearched" class="lit-empty">
            <el-icon :size="40" color="#d1d5db"><Search /></el-icon>
            <p>未找到相关文献，请尝试其他关键词</p>
          </div>
        </el-tab-pane>

        <!-- ====== 项目空间 ====== -->
        <el-tab-pane label="项目空间" name="projects">
          <el-row :gutter="12">
            <el-col :xs="24" :sm="12" :lg="8" v-for="p in projects" :key="p.id" style="margin-bottom:12px;">
              <el-card shadow="hover" class="proj-card" @click="selected = p">
                <div class="proj-top">
                  <div class="proj-icon" :style="{background: p.color + '12', color: p.color}">
                    <el-icon :size="20"><component :is="p.icon" /></el-icon>
                  </div>
                  <el-tag size="small" :type="p.status==='进行中'?'success':'info'" effect="light">{{ p.status }}</el-tag>
                </div>
                <h4>{{ p.name }}</h4>
                <p>{{ p.desc }}</p>
                <div class="proj-meta">
                  <span><UserFilled style="margin-right:3px;" />{{ p.members }} 人</span>
                  <span><Document style="margin-right:3px;" />{{ p.papers }} 篇</span>
                </div>
                <el-progress :percentage="p.progress" :stroke-width="5" :show-text="false" color="#1677ff" />
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

      </el-tabs>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="selected" title="项目详情" width="600px">
      <template v-if="selected">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="成员">{{ selected.members }} 人</el-descriptions-item>
          <el-descriptions-item label="论文">{{ selected.papers }} 篇</el-descriptions-item>
          <el-descriptions-item label="状态">{{ selected.status }}</el-descriptions-item>
          <el-descriptions-item label="进度"><el-progress :percentage="selected.progress" :stroke-width="8" style="width:160px;" /></el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selected.desc }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Lightning, Refresh, EditPen, DataAnalysis, Share, UserFilled, Document, Search, Reading, Star, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPost } from '../api.js'

const tab = ref('topics')
const selected = ref(null)

// ---- 加载状态 ----
const loading = reactive({
  generate: false,
  evaluate: false,
  search: false,
  projects: false,
})

// ---- 智能选题 ----
const topicInput = ref('')
const generatedTopics = ref([])

async function generateTopics() {
  if (!topicInput.value.trim()) { ElMessage.warning('请输入研究方向'); return }
  loading.generate = true
  try {
    const res = await apiPost('/api/research/generate', { input: topicInput.value })
    generatedTopics.value = res.data || res
    ElMessage.success('选题生成完成')
  } catch (e) {
    ElMessage.error('选题生成失败：' + (e.message || '未知错误'))
  } finally {
    loading.generate = false
  }
}

async function useTopic(t) {
  try {
    await apiPost('/api/research/adopt', { topic: t })
    ElMessage.success('已采用选题: ' + t.name)
  } catch (e) {
    ElMessage.info('已采用选题: ' + t.name)
  }
}

function evalTopic(t) {
  tab.value = 'evaluate'
  evalTopicTitle.value = t.name
  doEvaluate()
}

// ---- 选题测评 ----
const evalTopicTitle = ref('')
const evalResult = ref(null)

async function doEvaluate() {
  if (!evalTopicTitle.value.trim()) { ElMessage.warning('请输入选题名称'); return }
  loading.evaluate = true
  try {
    const res = await apiPost('/api/research/evaluate', { title: evalTopicTitle.value })
    evalResult.value = res.data || res
    ElMessage.success('测评完成')
  } catch (e) {
    ElMessage.error('测评失败：' + (e.message || '未知错误'))
  } finally {
    loading.evaluate = false
  }
}

// ---- 期刊方向 ----
const journals = ref([
  { id: 1, name: '中国社会科学', year: '2026', issue: '第3期', topic: '人工智能时代的社会治理创新' },
  { id: 2, name: '政治学研究', year: '2026', issue: '第2期', topic: '新时代党的建设理论与实践创新' },
  { id: 3, name: '管理世界', year: '2026', issue: '第5期', topic: '数字化转型与组织变革' },
  { id: 4, name: '中国工业经济', year: '2026', issue: '第4期', topic: '制造业高质量发展与产业升级' },
  { id: 5, name: '中国行政管理', year: '2026', issue: '第3期', topic: '数字政府建设与治理现代化' },
  { id: 6, name: '公共管理学报', year: '2026', issue: '第2期', topic: '基层治理现代化的路径与机制' },
])

// ---- 文献检索 ----
const litQuery = ref('')
const litSource = ref('all')
const litField = ref('keyword')
const litSearched = ref(false)
const litResults = ref([])

async function searchLiterature() {
  if (!litQuery.value.trim()) { ElMessage.warning('请输入检索关键词'); return }
  loading.search = true
  litSearched.value = true
  try {
    const res = await apiPost('/api/research/literature', {
      query: litQuery.value,
      source: litSource.value,
      field: litField.value,
    })
    litResults.value = res.data || res
    ElMessage.success('检索完成，共 ' + litResults.value.length + ' 条结果')
  } catch (e) {
    // Fallback: 如果后端接口不可用，使用本地模拟数据
    litResults.value = [
      { title: '人工智能赋能基层党建的创新路径研究', authors: '张三, 李四, 王五', journal: '党建研究', year: '2026', citations: 32, abstract: '本文探讨了人工智能技术在基层党建工作中的应用场景、实现路径与风险防控，提出了"数据驱动+精准服务"的党建新模式。' },
      { title: '数字化转型背景下国有企业党建工作创新研究', authors: '赵六, 钱七', journal: '国企管理', year: '2025', citations: 28, abstract: '基于对32家国有企业的调研数据，分析了数字化转型对党建工作的影响机制和创新方向。' },
      { title: '新时代党校干部教育数字化转型的理论逻辑与实践路径', authors: '孙八, 周九, 吴十', journal: '中国党政干部论坛', year: '2026', citations: 15, abstract: '从技术赋能和制度创新两个维度分析了党校培训数字化转型的驱动因素、关键瓶颈与实施路径。' },
      { title: 'AIGC在党建宣传中的应用探索与思考', authors: '郑一, 陈二', journal: '思想政治工作研究', year: '2025', citations: 21, abstract: '探索生成式AI在党建内容创作、传播方式优化、互动性提升等方面的应用案例与经验总结。' },
    ]
    ElMessage.success('检索完成（离线模式），共 ' + litResults.value.length + ' 条结果')
  } finally {
    loading.search = false
  }
}

// ---- 项目空间 ----
const projects = ref([])

onMounted(async () => {
  loading.projects = true
  try {
    const res = await apiGet('/api/research/projects')
    projects.value = res.data || res
  } catch (e) {
    // Fallback: 接口不可用时使用默认数据
    projects.value = [
      { id: 1, name: '新时代党建理论体系研究', desc: '构建党建工作理论框架', members: 5, papers: 12, status: '进行中', progress: 65, icon: 'Reading', color: '#1677ff' },
      { id: 2, name: '船舶工业高质量发展路径', desc: '高质量发展评估体系与实施路径', members: 8, papers: 20, status: '进行中', progress: 80, icon: 'TrendCharts', color: '#10b981' },
      { id: 3, name: '国企改革三年行动成效评估', desc: '量化评估研究', members: 3, papers: 6, status: '已完成', progress: 100, icon: 'DataAnalysis', color: '#f59e0b' },
      { id: 4, name: '基层党建数字化转型', desc: '数字化工具赋能党建创新', members: 4, papers: 3, status: '进行中', progress: 40, icon: 'Cpu', color: '#8b5cf6' },
      { id: 5, name: '企业党校教学创新研究', desc: '党校教学方法与模式创新', members: 6, papers: 8, status: '进行中', progress: 55, icon: 'Magnet', color: '#06b6d4' },
      { id: 6, name: '干部培训效果评估模型', desc: '培训投入产出量化分析框架', members: 2, papers: 4, status: '规划中', progress: 10, icon: 'SetUp', color: '#ec4899' },
    ]
  } finally {
    loading.projects = false
  }
})
</script>

<style scoped>
.research-card { border-radius: 8px; border: 1px solid var(--border-color); }
.research-tabs :deep(.el-tabs__item) { font-size: 14px; }

/* 智能选题 */
.topic-generator {
  background: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 16px;
}
.topic-generator h3 { margin: 0 0 4px; font-size: 16px; color: var(--text-main); }
.topic-generator p { color: #94a3b8; font-size: 13px; margin: 0 0 12px; }
.topic-actions { margin-top: 12px; display: flex; gap: 8px; }

.topic-results { margin-bottom: 16px; }
.topic-results h4 { font-size: 15px; margin: 0 0 12px; }
.topic-item {
  display: flex; gap: 14px; padding: 14px;
  background: #fff; border: 1px solid var(--border-color); border-radius: 8px;
  margin-bottom: 8px; transition: all .15s;
}
.topic-item:hover { border-color: #bae0ff; box-shadow: var(--shadow-card-hover); }
.topic-num {
  width: 28px; height: 28px; border-radius: 8px;
  background: #1677ff; color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.topic-body { flex: 1; }
.topic-name { font-size: 15px; font-weight: 600; color: var(--text-main); margin-bottom: 4px; }
.topic-desc { font-size: 13px; color: #4b5563; margin-bottom: 8px; }
.topic-tags { display: flex; gap: 6px; margin-bottom: 6px; }
.topic-ops { display: flex; gap: 8px; }

/* 期刊 */
.section-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.section-hd h4 { margin: 0; font-size: 15px; }
.journal-card { cursor: pointer; border-radius: 8px; border: 1px solid var(--border-color); }
.journal-card:hover { border-color: #bae0ff; }
.journal-name { font-weight: 600; font-size: 13px; color: var(--text-main); }
.journal-year { font-size: 11px; color: #94a3b8; margin: 4px 0; }
.journal-topic { font-size: 12px; color: #1677ff; font-style: italic; }

/* 选题测评 */
.eval-section { padding: 4px; }
.eval-section h3 { font-size: 16px; margin: 0 0 4px; }
.eval-section > p { color: #94a3b8; font-size: 13px; margin: 0 0 12px; }
.eval-result { margin-top: 20px; }
.eval-dim { text-align: center; border-radius: 8px; }
.dim-score { font-size: 32px; font-weight: 800; }
.dim-name { font-size: 13px; color: var(--text-secondary); margin: 4px 0 8px; }
.eval-advice { margin-top: 12px; border-radius: 8px; }

/* 项目 */
.proj-card { cursor: pointer; border-radius: 8px; border: 1px solid var(--border-color); }
.proj-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-card-hover); }
.proj-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.proj-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.proj-card h4 { margin: 0 0 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.proj-card p { color: #94a3b8; font-size: 12px; margin: 0 0 8px; line-height: 1.5; }
.proj-meta { display: flex; gap: 12px; font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.proj-meta span { display: inline-flex; align-items: center; }
</style>
