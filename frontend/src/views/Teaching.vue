<template>
  <div>
    <div class="csic-hero" style="background-image:url(https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=1200&q=80);">
      <div class="hero-content">
        <h2>教学工作台</h2>
        <p>课题选题 · 灵感激发 · 内容创作 · 知识库</p>
      </div>
    </div>

    <el-card shadow="never" class="teach-card">
      <el-tabs v-model="tab" class="teach-tabs">

        <!-- ====== 课题选题 ====== -->
        <el-tab-pane label="课题选题" name="topics">
          <div class="section-intro">
            <h3>教学课题选题</h3>
            <p>根据培训方向自动生成规范的党校教学课题，支持课题结构分析与优化</p>
          </div>

          <div class="gen-box">
            <el-input v-model="topicInput" placeholder="输入培训方向或目标，如：党的二十大精神专题培训、中青年干部能力提升..." />
            <div class="gen-options">
              <span style="font-size:13px;color:#94a3b8;">课题深度：</span>
              <el-radio-group v-model="topicDepth" size="small">
                <el-radio-button value="basic">基础入门</el-radio-button>
                <el-radio-button value="medium">标准深度</el-radio-button>
                <el-radio-button value="deep">深入专题</el-radio-button>
              </el-radio-group>
            </div>
            <el-button type="primary" :icon="Lightning" @click="genTopics" style="margin-top:10px;">生成课题</el-button>
          </div>

          <div v-if="generatedTopics.length" class="result-section">
            <h4>推荐课题（{{ generatedTopics.length }} 个）</h4>
            <div v-for="(t, i) in generatedTopics" :key="i" class="result-item">
              <div class="result-badge">{{ i + 1 }}</div>
              <div class="result-body">
                <div class="result-title">{{ t.title }}</div>
                <div class="result-desc">{{ t.desc }}</div>
                <div class="result-tags">
                  <el-tag size="small" effect="light" type="primary">{{ t.level }}</el-tag>
                  <el-tag size="small" effect="light" type="warning">{{ t.hours }} 课时</el-tag>
                  <el-tag size="small" effect="light" type="success">适用：{{ t.audience }}</el-tag>
                </div>
                <div class="result-ops">
                  <el-button link type="primary" size="small" :icon="EditPen" @click="useTopic(t)">采用</el-button>
                  <el-button link type="primary" size="small" :icon="DataBoard" @click="inspireTopic(t)">灵感激发</el-button>
                  <el-button link size="small" :icon="FolderOpened" @click="enrichTopic(t)">丰富内容</el-button>
                  <el-button link size="small" :icon="Share" @click="ElMessage.success('已复制')">分享</el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- ====== 灵感激发 ====== -->
        <el-tab-pane label="灵感激发" name="inspire">
          <div class="section-intro">
            <h3>教学灵感激发</h3>
            <p>选择一个课题，AI 为您生成案例素材、互动设计、课堂活动等教学灵感</p>
          </div>

          <div class="gen-box" style="display:flex;gap:10px;align-items:flex-start;">
            <el-select v-model="inspireTopic" placeholder="选择或输入课题" style="width:280px;" filterable allow-create>
              <el-option v-for="t in allTopics" :key="t" :label="t" :value="t" />
            </el-select>
            <el-select v-model="inspireType" placeholder="灵感类型" style="width:160px;">
              <el-option label="案例素材" value="case" />
              <el-option label="互动设计" value="interactive" />
              <el-option label="课堂活动" value="activity" />
              <el-option label="讨论议题" value="discussion" />
              <el-option label="考核方式" value="exam" />
            </el-select>
            <el-button type="primary" :icon="DataBoard" @click="genInspire">激发灵感</el-button>
          </div>

          <div v-if="inspirations.length" class="inspire-list">
            <div v-for="(item, i) in inspirations" :key="i" class="inspire-item">
              <div class="inspire-icon">
                <el-icon :size="22" :color="item.color"><component :is="item.icon" /></el-icon>
              </div>
              <div class="inspire-body">
                <div class="inspire-title">{{ item.title }}</div>
                <div class="inspire-detail">{{ item.detail }}</div>
              </div>
              <el-button link type="primary" size="small" :icon="FolderOpened" @click="ElMessage.success('已采纳')">采纳</el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- ====== 内容创作 ====== -->
        <el-tab-pane label="内容创作" name="content">
          <div class="section-intro">
            <h3>课题内容丰富</h3>
            <p>基于已有课题框架，生成课件大纲、逐页讲稿、案例材料等教学资源</p>
          </div>

          <div class="gen-box">
            <el-select v-model="contentTopic" placeholder="选择课题" style="width:100%;margin-bottom:10px;" filterable>
              <el-option v-for="t in allTopics" :key="t" :label="t" :value="t" />
            </el-select>
            <el-checkbox-group v-model="contentTypes" class="content-types">
              <el-checkbox label="outline" value="outline">课件大纲</el-checkbox>
              <el-checkbox label="lecture" value="lecture">逐页讲稿</el-checkbox>
              <el-checkbox label="slides" value="slides">PPT 提纲</el-checkbox>
            </el-checkbox-group>
            <div class="kb-attach" v-if="kbs.length">
              <span style="font-size:13px;color:#4b5563;font-weight:500;">挂载知识库：</span>
              <el-select v-model="attachKb" placeholder="选择知识库" style="width:200px;" clearable>
                <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
              </el-select>
              <span style="font-size:11px;color:#94a3b8;margin-left:6px;">知识库内容将作为生成素材的参考来源</span>
            </div>
            <el-button type="primary" :icon="EditPen" @click="genContent" style="margin-top:10px;">开始创作</el-button>
          </div>

          <div v-if="contentResult" class="content-preview">
            <el-tabs v-model="contentResultTab">
              <el-tab-pane v-for="(ct, ctKey) in contentResult" :key="ctKey" :label="ct.label" :name="ctKey">
                <div class="content-text">{{ ct.text }}</div>
              </el-tab-pane>
            </el-tabs>
            <div style="margin-top:10px;display:flex;gap:8px;">
              <el-button size="small" :icon="Download">导出 Word</el-button>
              <el-button size="small" :icon="Share">分享</el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- ====== 知识库 ====== -->
        <el-tab-pane label="数据包下载" name="download">
          <div class="section-intro">
            <h3>教学数据包下载</h3>
            <p>一键下载课题相关的完整教学资源包（课件大纲 + 讲稿 + PPT 提纲）</p>
          </div>
          <el-table :data="dataPacks" stripe>
            <el-table-column prop="name" label="数据包名称" min-width="260" />
            <el-table-column prop="type" label="内容" width="200" />
            <el-table-column prop="size" label="大小" width="100" />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" :icon="Download" @click="downloadPack(row)">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="教学知识库" name="kb">
          <div class="section-intro">
            <h3>教学知识库</h3>
            <p>管理和挂载教学资源库，课件、案例、试题一键调用</p>
          </div>

          <el-table :data="kbs" stripe>
            <el-table-column prop="name" label="知识库名称" min-width="200" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }"><el-tag size="small" effect="light">{{ row.type }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="docs" label="文档数" width="80" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="attachKb = row.id; ElMessage.success('已挂载: ' + row.name)">挂载到创作</el-button>
                <el-button link size="small">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Lightning, EditPen, DataBoard, FolderOpened, Share, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiPost } from '../api.js'

const tab = ref('topics')

// ---- 加载状态 ----
const loading = ref({
  topics: false,
  inspire: false,
  content: false,
})

// ---- 课题选题 ----
const topicInput = ref('')
const topicDepth = ref('medium')
const generatedTopics = ref([])

const allTopics = computed(() => generatedTopics.value.map(t => t.title))

async function genTopics() {
  if (!topicInput.value.trim()) { ElMessage.warning('请输入培训方向'); return }
  loading.value.topics = true
  try {
    const res = await apiPost('/api/teaching/generate', {
      input: topicInput.value,
      depth: topicDepth.value,
    })
    generatedTopics.value = res.data || res
    ElMessage.success('课题生成完成')
  } catch (e) {
    ElMessage.error('课题生成失败：' + (e.message || '未知错误'))
  } finally {
    loading.value.topics = false
  }
}

function useTopic(t) { ElMessage.success('已采用课题: ' + t.title) }

// ---- 灵感激发 ----
const inspireTopic = ref('')
const inspireType = ref('case')
const inspirations = ref([])

async function genInspire() {
  if (!inspireTopic.value) { ElMessage.warning('请选择课题'); return }
  loading.value.inspire = true
  try {
    const res = await apiPost('/api/teaching/inspire', {
      topic_id: inspireTopic.value,
      type: inspireType.value,
    })
    inspirations.value = res.data || res
    ElMessage.success('灵感生成完成')
  } catch (e) {
    ElMessage.error('灵感生成失败：' + (e.message || '未知错误'))
  } finally {
    loading.value.inspire = false
  }
}

// ---- 内容创作 ----
const contentTopic = ref('')
const contentTypes = ref(['outline', 'lecture'])
const contentResult = ref(null)
const contentResultTab = ref('outline')
const attachKb = ref('')

async function genContent() {
  if (!contentTopic.value) { ElMessage.warning('请选择课题'); return }
  loading.value.content = true
  try {
    const res = await apiPost('/api/teaching/content', {
      topic_id: contentTopic.value,
      content_types: [...contentTypes.value],
    })
    contentResult.value = res.data || res
    contentResultTab.value = Object.keys(contentResult.value)[0]
    ElMessage.success('内容生成完成' + (attachKb.value ? '，已挂载知识库 ✓' : ''))
  } catch (e) {
    ElMessage.error('内容生成失败：' + (e.message || '未知错误'))
  } finally {
    loading.value.content = false
  }
}

// ---- 教学知识库 ----
const kbs = ref([
  { id: 1, name: '二十大精神学习资料汇编', type: '课件', docs: 45 },
  { id: 2, name: '干部培训案例库', type: '案例', docs: 128 },
  { id: 3, name: '党校精品课程库', type: '课程', docs: 36 },
  { id: 4, name: '政策法规教学参考', type: '参考', docs: 72 },
  { id: 5, name: '党史教育素材库', type: '素材', docs: 89 },
])

// ---- 数据包下载 ----
const dataPacks = ref([
  { name: '党的二十大精神解读 - 完整教学包', type: '课件大纲 + 讲稿 + PPT', size: '8.5 MB' },
  { name: '领导干部数字素养 - 教学资源包', type: '课件大纲 + 讲稿', size: '5.2 MB' },
  { name: '国企党建与业务融合 - 案例教学包', type: '课件大纲 + 案例材料 + PPT', size: '12.8 MB' },
  { name: '中国式现代化理论 - 专题教学包', type: '逐页讲稿 + PPT 提纲', size: '6.7 MB' },
  { name: '基层党建工作方法 - 工具教学包', type: '课件大纲 + 讲稿 + 配套素材', size: '10.3 MB' },
])

function downloadPack(row) {
  // 模拟下载，实际应接入文件下载API
  ElMessage.success('开始下载: ' + row.name)
}

// ---- 初始化 ----
onMounted(async () => {
  try {
    const res = await apiGet('/api/teaching/topics')
    generatedTopics.value = res.data || res
  } catch (e) {
    // 接口不可用时忽略，用户手动生成课题
  }
})
</script>

<style scoped>
.teach-card { border-radius: 8px; border: 1px solid var(--border-color); }
.teach-tabs :deep(.el-tabs__item) { font-size: 14px; }

.section-intro { margin-bottom: 16px; }
.section-intro h3 { margin: 0 0 2px; font-size: 16px; color: var(--text-main); }
.section-intro p { color: #94a3b8; font-size: 13px; margin: 0; }

.gen-box {
  background: #f8fafc; border-radius: 8px; padding: 18px;
  margin-bottom: 18px;
}
.gen-options { margin-top: 10px; display: flex; align-items: center; gap: 8px; }

.result-section { margin-bottom: 16px; }
.result-section h4 { font-size: 15px; margin: 0 0 10px; }

.result-item {
  display: flex; gap: 14px; padding: 14px;
  background: #fff; border: 1px solid var(--border-color); border-radius: 8px;
  margin-bottom: 8px; transition: all .15s;
}
.result-item:hover { border-color: #bae0ff; box-shadow: var(--shadow-card-hover); }
.result-badge {
  width: 28px; height: 28px; border-radius: 8px;
  background: #1677ff; color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.result-body { flex: 1; }
.result-title { font-size: 15px; font-weight: 600; color: var(--text-main); margin-bottom: 4px; }
.result-desc { font-size: 13px; color: #4b5563; margin-bottom: 8px; }
.result-tags { display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
.result-ops { display: flex; gap: 8px; flex-wrap: wrap; }

/* 灵感 */
.inspire-list { display: flex; flex-direction: column; gap: 8px; }
.inspire-item {
  display: flex; gap: 14px; align-items: flex-start;
  background: #fff; border: 1px solid var(--border-color); border-radius: 8px;
  padding: 14px; transition: all .15s;
}
.inspire-item:hover { border-color: #bae0ff; }
.inspire-icon {
  width: 42px; height: 42px; border-radius: 10px;
  background: #f8fafc; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.inspire-body { flex: 1; }
.inspire-title { font-weight: 600; font-size: 14px; color: var(--text-main); margin-bottom: 4px; }
.inspire-detail { font-size: 13px; color: #4b5563; line-height: 1.6; }

/* 内容创作 */
.content-types { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
.kb-attach { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
.content-preview { margin-top: 12px; }
.content-text {
  background: #f8fafc; border-radius: 6px; padding: 14px;
  white-space: pre-wrap; font-size: 13px; line-height: 1.7;
  max-height: 360px; overflow-y: auto;
}
</style>
