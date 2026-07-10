<template>
  <div>
    <div class="r-topbar">
      <div class="r-title">科研工作台</div>
      <div class="r-tabs">
        <div v-for="t in tabs" :key="t.id" :class="['r-tab',{active:t.id===tab}]" @click="tab=t.id">
          <el-icon :size="16"><component :is="t.icon" /></el-icon>{{ t.label }}
        </div>
        <el-select v-if="tab==='chat'" v-model="model" size="small" style="width:110px;margin-left:auto">
          <el-option v-for="m in models" :key="m" :label="m" :value="m" />
        </el-select>
        <el-select v-if="tab==='chat'" v-model="kbId" size="small" style="width:140px;margin-left:4px" clearable placeholder="Dify知识库">
          <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id"><span>{{ kb.name }}</span><span style="color:#bbb;font-size:10px;margin-left:6px">{{ kb.count }}篇</span></el-option>
        </el-select>
      </div>
    </div>

    <div class="r-body">
      <!-- Tab 1: 学术对话 -->
      <div v-if="tab==='chat'" class="full-chat">
        <div class="chat-side">
          <div class="func-group-label">论文处理</div>
          <div v-for="f in paperFuncs" :key="f.id" class="side-func" @click="chatInput=f.placeholder;focusInput()"><el-icon :size="13"><component :is="f.icon" /></el-icon>{{ f.label }}</div>
          <div class="func-group-label" style="margin-top:8px">学术写作</div>
          <div v-for="f in writeFuncs" :key="f.id" class="side-func" @click="chatInput=f.placeholder;focusInput()"><el-icon :size="13"><component :is="f.icon" /></el-icon>{{ f.label }}</div>
          <div class="func-group-label" style="margin-top:8px">研究工具</div>
          <div v-for="f in toolFuncs" :key="f.id" class="side-func" @click="chatInput=f.placeholder;focusInput()"><el-icon :size="13"><component :is="f.icon" /></el-icon>{{ f.label }}</div>
          <div style="height:1px;background:#e5e7eb;margin:6px 0"></div>
          <el-button type="primary" :icon="Plus" size="small" class="new-btn" @click="newConv">新建对话</el-button>
          <div class="hist-list">
            <div v-for="c in convs" :key="c.id" class="hist-item" :class="{active:c.id===convId}" @click="loadConv(c)">
              <span class="hist-title">{{ c.title||'对话' }}</span>
              <el-dropdown trigger="click" @command="(cmd)=>histAction(cmd,c)"><el-button link size="small" class="hist-more" @click.stop><el-icon><MoreFilled /></el-icon></el-button>
                <template #dropdown><el-dropdown-menu>
                  <el-dropdown-item command="rename"><el-icon><EditPen /></el-icon>重命名</el-dropdown-item>
                  <el-dropdown-item command="docx"><el-icon><Download /></el-icon>保存docx</el-dropdown-item>
                  <el-dropdown-item command="skill"><el-icon><MagicStick /></el-icon>整理技能</el-dropdown-item>
                  <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon>删除</el-dropdown-item>
                </el-dropdown-menu></template>
              </el-dropdown>
            </div><div v-if="!convs.length" style="color:#bbb;font-size:11px;text-align:center;padding:10px">暂无历史</div>
          </div>
        </div>
        <div class="chat-main">
          <div class="chat-body" ref="chatBody">
            <div v-if="chatMsgs.length===0" class="empty">输入研究方向开始学术对话</div>
            <div v-for="(m,i) in chatMsgs" :key="i" :class="['msg',m.role]"><div class="msg-text" v-html="render(m.content)"></div></div>
            <div v-if="chatLoading" class="msg assistant"><div class="msg-text">...</div></div>
          </div>
          <div class="chat-input-wrap">
            <el-upload :show-file-list="false" :before-upload="handleUpload" accept=".pdf,.docx,.txt,.md"><el-button circle size="small"><el-icon><UploadFilled /></el-icon></el-button></el-upload>
            <el-input v-model="chatInput" type="textarea" :rows="3" placeholder="输入研究方向或学术问题..." @keydown.enter.exact.prevent="chatSend" resize="none" />
            <el-button type="primary" @click="chatSend" :loading="chatLoading" size="small">发送</el-button>
          </div>
        </div>
        <div class="chat-skill">
          <div class="skill-label">技能</div>
          <div class="skill-list" v-if="skillList.length"><div v-for="s in skillList" :key="s.id" class="skill-row" :class="{active:s.id===skillId}" @click="skillId=s.id;ElMessage.success('已挂载: '+s.name)"><el-icon :size="13"><component :is="iconMap[s.icon]||MagicStick" /></el-icon><span>{{ s.name }}</span></div></div>
        </div>
      </div>

      <!-- Tab 2: 论文阅读 — PyPDF2 + Arxiv + AI -->
      <div v-if="tab==='read'" class="func-panel">
        <div class="panel-split">
          <div class="panel-left">
            <div class="panel-title">📄 上传 PDF（PyPDF2 真实解析）</div>
            <el-upload :show-file-list="false" :before-upload="uploadPaper" accept=".pdf" drag><el-icon :size="32"><UploadFilled /></el-icon><p>点击或拖拽PDF</p></el-upload>
            <el-divider />
            <div class="panel-title">🔗 Arxiv 论文（真实 API）</div>
            <el-input v-model="arxivUrl" placeholder="粘贴Arxiv链接" size="small" /><el-button size="small" style="margin-top:6px;width:100%" @click="fetchArxiv" :disabled="!arxivUrl" :loading="readLoading">获取并解读</el-button>
            <el-divider />
            <div class="panel-title">📝 粘贴文本</div>
            <el-input v-model="paperText" type="textarea" :rows="6" placeholder="粘贴论文内容..." size="small" />
            <el-select v-model="readMode" size="small" style="width:100%;margin:6px 0">
              <el-option label="深度解读" value="read" /><el-option label="论文评审" value="review" /><el-option label="翻译" value="translate" />
            </el-select>
            <el-button type="primary" size="small" style="width:100%" @click="analyzePaper" :disabled="!paperText" :loading="readLoading">分析</el-button>
          </div>
          <div class="panel-right"><div class="result-box" ref="readBody"><div v-if="!readResult && !readLoading" class="empty">在左侧上传PDF或粘贴论文开始分析</div><div v-else class="result-text" v-html="render(readResult)"></div><div v-if="readLoading" style="color:#bbb;padding:10px">分析中...</div></div></div>
        </div>
      </div>

      <!-- Tab 3: 学术写作 -->
      <div v-if="tab==='write'" class="func-panel">
        <div class="panel-split">
          <div class="panel-left" style="width:280px;min-width:280px">
            <div class="panel-title">选择写作任务</div>
            <div v-for="f in writeFuncs" :key="f.id" class="write-task" :class="{active:f.id===writeTask}" @click="writeTask=f.id;writeInput=''">
              <el-icon :size="14"><component :is="f.icon" /></el-icon>{{ f.label }}
            </div>
            <el-input v-model="writeInput" type="textarea" :rows="3" :placeholder="writeFuncs.find(f=>f.id===writeTask)?.placeholder" size="small" style="margin-top:8px" />
            <el-button type="primary" size="small" style="width:100%;margin-top:6px" @click="doWrite" :loading="writeLoading" :disabled="!writeInput">开始写作</el-button>
          </div>
          <div class="panel-right"><div class="result-box" ref="writeBody"><div v-if="!writeResult && !writeLoading" class="empty">选择任务开始AI写作</div><div v-else class="result-text" v-html="render(writeResult)"></div><div v-if="writeLoading" style="color:#bbb;padding:10px">写作中...</div></div></div>
        </div>
      </div>

      <!-- Tab 4: 文献检索 — AMiner + Arxiv 真实搜索 -->
      <div v-if="tab==='search'" class="func-panel">
        <div class="panel-split">
          <div class="panel-left">
            <div class="panel-title">🔍 AI增强学术搜索</div>
            <el-alert title="搜索流程：AMiner学者 API → Arxiv论文 API → AI分析" type="success" :closable="false" show-icon style="margin-bottom:8px;font-size:11px" />
            <el-input v-model="searchQuery" placeholder="输入搜索主题..." size="small" @keydown.enter="doSearch" />
            <el-select v-model="searchType" size="small" style="width:100%;margin:6px 0">
              <el-option label="综合搜索（AMiner+Arxiv+AI）" value="search" />
              <el-option label="技术趋势分析" value="trend" />
            </el-select>
            <el-button type="primary" size="small" style="width:100%" @click="doSearch" :loading="searchLoading" :disabled="!searchQuery">开始检索</el-button>
          </div>
          <div class="panel-right"><div class="result-box" ref="searchBody"><div v-if="!searchResult && !searchLoading" class="empty">输入主题开始检索<br>AMiner(学者) + Arxiv(论文) + AI分析</div><div v-else class="result-text" v-html="render(searchResult)"></div><div v-if="searchLoading" style="color:#bbb;padding:10px">检索中...</div></div></div>
        </div>
      </div>

      <!-- Tab 5: 投稿选刊 — 内置20本核心期刊 + AI推荐 -->
      <div v-if="tab==='journal'" class="func-panel">
        <div class="panel-split">
          <div class="panel-left">
            <div class="panel-title">📰 投稿选刊推荐</div>
            <el-alert title="内置20本核心期刊数据库（党建/管理/船舶/科技）+ AI智能匹配" type="success" :closable="false" show-icon style="margin-bottom:8px;font-size:11px" />
            <el-input v-model="journalTitle" placeholder="论文标题" size="small" />
            <el-input v-model="journalField" placeholder="研究领域" size="small" style="margin-top:6px" />
            <el-input v-model="journalAbstract" type="textarea" :rows="4" placeholder="论文摘要（可选）" size="small" style="margin-top:6px" />
            <el-button type="primary" size="small" style="width:100%;margin-top:6px" @click="doJournalRecommend" :loading="journalLoading" :disabled="!journalTitle&&!journalField">推荐期刊</el-button>
          </div>
          <div class="panel-right"><div class="result-box" ref="journalBody"><div v-if="!journalResult && !journalLoading" class="empty">输入论文标题/领域，获取投稿建议<br>内置期刊库 + AI 智能匹配</div><div v-else class="result-text" v-html="render(journalResult)"></div><div v-if="journalLoading" style="color:#bbb;padding:10px">分析中...</div></div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { apiGet, apiDelete, apiPost } from '../api.js'
import * as Icons from '@element-plus/icons-vue'
import { marked } from 'marked'
import { Plus, UploadFilled, MoreFilled, EditPen, Download, Delete, MagicStick, TrendCharts, Reading, Search, Promotion, Document, DataAnalysis, Files, Connection, Notebook } from '@element-plus/icons-vue'
const iconMap = { ...Icons }

const tabs = [{id:'chat',label:'学术对话',icon:TrendCharts},{id:'read',label:'论文阅读',icon:Reading},{id:'write',label:'学术写作',icon:EditPen},{id:'search',label:'文献检索',icon:Search},{id:'journal',label:'投稿选刊',icon:Promotion}]
const tab = ref('chat'), model = ref('deepseek'), models = ['deepseek','qwen','zhipu','kimi','minimax','doubao']
const B = location.port==='5173'?'http://localhost:8000':''

// Functions
const paperFuncs = [{id:'read',label:'论文解读',icon:Reading,placeholder:'请粘贴论文内容进行深度解读'},{id:'review',label:'论文评审',icon:Document,placeholder:'请粘贴论文进行学术评审'},{id:'translate',label:'论文翻译',icon:Connection,placeholder:'请粘贴需要翻译的学术文本'}]
const writeFuncs = [{id:'topics',label:'选题生成',icon:MagicStick,placeholder:'请输入研究方向'},{id:'paper',label:'一键范文',icon:Notebook,placeholder:'请输入论文课题名称'},{id:'outline',label:'论文大纲',icon:Document,placeholder:'请输入论文课题'},{id:'review_lit',label:'文献综述',icon:Files,placeholder:'请输入综述主题'},{id:'polish',label:'文本润色',icon:EditPen,placeholder:'请粘贴需要润色的文本'}]
const toolFuncs = [{id:'evaluate',label:'选题测评',icon:DataAnalysis,placeholder:'请输入要评估的选题'},{id:'search',label:'学术搜索',icon:Search,placeholder:'请输入搜索主题'},{id:'trend',label:'趋势分析',icon:TrendCharts,placeholder:'请输入研究领域'}]

// Chat
const chatInput = ref(''), chatMsgs = ref([]), chatLoading = ref(false), chatBody = ref(null), skillId = ref(''), skillList = ref([]), convs = ref([]), convId = ref('new'), kbId = ref(''), kbList = ref([])

onMounted(async ()=>{
  const [s,c,k] = await Promise.all([apiGet('/api/skills'), apiGet('/api/research-chat/conversations'), apiGet('/api/dify/datasets/list')])
  if(s) skillList.value = s; if(c) convs.value = c.map(x=>({id:x.id,title:x.title||'对话',time:x.created_at?.slice(0,10)||''}))
  if(k) kbList.value = k
})
function newConv(){ convId.value='new'; chatMsgs.value=[] }
async function loadConv(c){ convId.value=c.id; const d=await apiGet(`/api/research-chat/conversations/${c.id}/messages`); chatMsgs.value=d?d.map(m=>({role:m.role,content:m.content})):[] }
async function refreshConvs(){ const c=await apiGet('/api/research-chat/conversations'); if(c) convs.value=c.map(x=>({id:x.id,title:x.title||'对话',time:x.created_at?.slice(0,10)||''})) }
async function histAction(cmd,c){
  if(cmd==='rename'){ try{ const{value}=await import('element-plus').then(m=>m.ElMessageBox.prompt('新名称','重命名',{inputValue:c.title})); if(value?.trim()){ const t=localStorage.getItem('csic_token'); await fetch(`${B}/api/research-chat/conversations/${c.id}/rename`,{method:'PUT',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({title:value.trim()})}); c.title=value.trim(); ElMessage.success('已重命名') } } catch{} }
  else if(cmd==='delete'){ await apiDelete(`/api/research-chat/conversations/${c.id}`); convs.value=convs.value.filter(x=>x.id!==c.id); if(convId.value===c.id){ convId.value='new'; chatMsgs.value=[] } }
  else if(cmd==='docx'){ const t=localStorage.getItem('csic_token'); try{ const r=await fetch(`${B}/api/export/docx`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({conversation_id:c.id})}); if(r.ok){ const b=await r.blob(); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=`${c.title||'对话'}.docx`; a.click() } } catch(e){} }
  else if(cmd==='skill'){ const d=await apiGet(`/api/research-chat/conversations/${c.id}/messages`); const content=d?d.map(m=>`### ${m.role}\n${m.content}`).join('\n\n'):c.title; await apiPost('/api/skills',{name:c.title||'新技能',description:'对话提炼',category:'科研',icon:'MagicStick',color:'#1677ff',prompt:`基于以下对话内容：\n\n${content.slice(0,3000)}`}); ElMessage.success('已整理') }
}

async function chatSend(){
  const t=chatInput.value.trim(); if(!t||chatLoading.value)return
  chatMsgs.value.push({role:'user',content:t}); chatInput.value=''; chatLoading.value=true
  chatMsgs.value.push({role:'assistant',content:''}); const last=chatMsgs.value[chatMsgs.value.length-1]
  const token=localStorage.getItem('csic_token')
  try{
    const r=await fetch(`${B}/api/research-chat/send`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({query:t,model:model.value,skill_id:skillId.value||'',conversation_id:convId.value})})
    const reader=r.body.getReader(); const dec=new TextDecoder()
    while(true){ const{done,value}=await reader.read(); if(done)break; for(const l of dec.decode(value,{stream:true}).split('\n')){ if(l.startsWith('data: ')){ const d=l.slice(6); if(d==='[DONE]')continue; try{ const j=JSON.parse(d); if(j.content)last.content+=j.content; if(j.conversation_id&&convId.value==='new'){ convId.value=j.conversation_id; refreshConvs() } } catch{} } } }
  }catch(e){ last.content=`[错误] ${e.message}` }
  finally{ chatLoading.value=false; await nextTick(); if(chatBody.value)chatBody.value.scrollTop=chatBody.value.scrollHeight }
}

async function handleUpload(file){ const fd=new FormData();fd.append('file',file);chatMsgs.value.push({role:'user',content:`📎 ${file.name}`});chatLoading.value=true;const t=localStorage.getItem('csic_token');try{const r=await fetch(`${B}/api/files/upload`,{method:'POST',headers:{Authorization:`Bearer ${t}`},body:fd});const d=await r.json();chatMsgs.value.push({role:'assistant',content:`已上传: ${(d.result||'').slice(0,1500)}`})}catch(e){chatMsgs.value.push({role:'assistant',content:'[上传失败]'})}finally{chatLoading.value=false};return false}
function focusInput(){ nextTick(()=>{ const ta=document.querySelector('.chat-input-wrap textarea'); if(ta)ta.focus() }) }

// Tab 2: 论文阅读
const readMode=ref('read'),paperText=ref(''),arxivUrl=ref(''),readResult=ref(''),readLoading=ref(false)
async function sseRead(r, target){ const reader=r.body.getReader();const dec=new TextDecoder();while(true){const{done,value}=await reader.read();if(done)break;for(const l of dec.decode(value,{stream:true}).split('\n')){if(l.startsWith('data: ')){const d=l.slice(6);if(d==='[DONE]')continue;try{target.value+=JSON.parse(d).content}catch{}}}}}
async function uploadPaper(file){ const fd=new FormData();fd.append('file',file);fd.append('func',readMode.value);readResult.value='';readLoading.value=true;const t=localStorage.getItem('csic_token');try{const r=await fetch(`${B}/api/research/upload-paper`,{method:'POST',headers:{Authorization:`Bearer ${t}`},body:fd});await sseRead(r,readResult)}catch(e){readResult.value=`[错误] ${e.message}`}finally{readLoading.value=false};return false}
async function analyzePaper(){ const fd=new FormData();fd.append('query',paperText.value);fd.append('model',model.value);const ep=readMode.value==='review'?'/api/research/paper-review':'/api/research/paper-read';readResult.value='';readLoading.value=true;const t=localStorage.getItem('csic_token');try{const r=await fetch(`${B}${ep}`,{method:'POST',headers:{Authorization:`Bearer ${t}`},body:fd});await sseRead(r,readResult)}catch(e){readResult.value=`[错误] ${e.message}`}finally{readLoading.value=false}}
async function fetchArxiv(){ const fd=new FormData();fd.append('url',arxivUrl.value);fd.append('model',model.value);readResult.value='';readLoading.value=true;const t=localStorage.getItem('csic_token');try{const r=await fetch(`${B}/api/research/arxiv`,{method:'POST',headers:{Authorization:`Bearer ${t}`},body:fd});await sseRead(r,readResult)}catch(e){readResult.value=`[错误] ${e.message}`}finally{readLoading.value=false}}

// Tab 3: 学术写作
const writeTask=ref('topics'),writeInput=ref(''),writeResult=ref(''),writeLoading=ref(false)
async function doWrite(){ const ep=writeTask.value==='paper'?'/api/research/generate-paper':'/api/research/stream';writeResult.value='';writeLoading.value=true;const t=localStorage.getItem('csic_token');try{const r=await fetch(`${B}${ep}`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({query:writeInput.value,model:model.value,function:writeTask.value})});await sseRead(r,writeResult)}catch(e){writeResult.value=`[错误] ${e.message}`}finally{writeLoading.value=false}}

// Tab 4: 文献检索 — 真实 AMiner+Arxiv+AI 三层检索
const searchQuery=ref(''),searchType=ref('search'),searchResult=ref(''),searchLoading=ref(false)
async function doSearch(){
  if(!searchQuery.value.trim()||searchLoading.value) return
  searchResult.value=''; searchLoading.value=true
  const t=localStorage.getItem('csic_token'); const ep=searchType.value==='trend'?'/api/research/trend-analysis':'/api/research/search'
  const fd=new FormData(); fd.append('query',searchQuery.value); fd.append('model',model.value)
  try{ const r=await fetch(`${B}${ep}`,{method:'POST',headers:{Authorization:`Bearer ${t}`},body:fd}); await sseRead(r,searchResult) }
  catch(e){ searchResult.value=`[错误] ${e.message}` } finally{ searchLoading.value=false }
}

// Tab 5: 投稿选刊 — 内置期刊库+AI推荐
const journalTitle=ref(''),journalField=ref(''),journalAbstract=ref(''),journalResult=ref(''),journalLoading=ref(false)
async function doJournalRecommend(){
  if(!journalTitle.value.trim()&&!journalField.value.trim()) return
  journalResult.value=''; journalLoading.value=true
  const t=localStorage.getItem('csic_token'); const fd=new FormData()
  fd.append('title',journalTitle.value); fd.append('field',journalField.value); fd.append('abstract',journalAbstract.value); fd.append('model',model.value)
  try{ const r=await fetch(`${B}/api/research/journal-recommend`,{method:'POST',headers:{Authorization:`Bearer ${t}`},body:fd}); await sseRead(r,journalResult) }
  catch(e){ journalResult.value=`[错误] ${e.message}` } finally{ journalLoading.value=false }
}

function render(t){ if(!t)return''; try{return marked.parse(t.replace(/\n{3,}/g,'\n\n'))}catch{return t} }
</script>

<style scoped>
.r-topbar{display:flex;align-items:center;padding:10px 16px;background:#fff;border-bottom:1px solid #e5e7eb;gap:16px}
.r-title{font-size:15px;font-weight:700;color:#1f2937}
.r-tabs{display:flex;align-items:center;gap:0}
.r-tab{display:flex;align-items:center;gap:6px;padding:8px 18px;cursor:pointer;font-size:13px;font-weight:500;color:#6b7280;border-bottom:3px solid transparent;transition:all .15s;margin-bottom:-1px}
.r-tab:hover{color:#1677ff}.r-tab.active{color:#1677ff;font-weight:600;border-bottom-color:#1677ff}
.r-body{height:calc(100vh - 200px);overflow:hidden}
.full-chat{display:flex;height:100%}
.chat-side{width:180px;min-width:180px;background:#f8f9fb;border-right:1px solid #e5e7eb;padding:8px;display:flex;flex-direction:column}
.func-group-label{font-size:10px;color:#bbb;text-transform:uppercase;font-weight:600;padding:2px 4px}
.side-func{display:flex;align-items:center;gap:4px;padding:4px 6px;border-radius:4px;cursor:pointer;font-size:11px;color:#374151;margin-bottom:1px}
.side-func:hover{background:#e8ecf1}
.new-btn{width:100%;margin-bottom:6px;margin-top:4px}
.hist-list{flex:1;overflow-y:auto}
.hist-item{padding:6px 8px;border-radius:6px;cursor:pointer;font-size:12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:2px}
.hist-title{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#374151}
.hist-item:hover,.hist-item.active{background:#f0f5ff}
.hist-more{opacity:0}.hist-item:hover .hist-more{opacity:1}
.chat-main{flex:1;display:flex;flex-direction:column;min-width:0}
.chat-body{flex:1;overflow-y:auto;padding:10px 20px}
.msg{margin-bottom:10px}.msg.user{text-align:right}
.msg-text{display:inline-block;max-width:80%;padding:7px 12px;border-radius:10px;font-size:13px;line-height:1.7;word-break:break-word}
.msg.user .msg-text{background:#1677ff;color:#fff}.msg.assistant .msg-text{background:#f3f4f6;color:#1f2937}
.chat-input-wrap{padding:8px 12px;border-top:1px solid #e5e7eb;display:flex;gap:6px;align-items:center}
.chat-input-wrap :deep(.el-textarea__inner){border-radius:8px;font-size:13px}
.chat-skill{width:150px;min-width:150px;background:#f8f9fb;border-left:1px solid #e5e7eb;padding:8px;overflow:hidden;display:flex;flex-direction:column}
.skill-label{font-size:10px;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:6px}
.skill-list{flex:1;overflow-y:auto}
.skill-row{display:flex;align-items:center;gap:4px;padding:4px 6px;border-radius:4px;cursor:pointer;font-size:11px;color:#374151;margin-bottom:2px}
.skill-row:hover{background:#e8ecf1}.skill-row.active{background:#1677ff12;color:#1677ff}
.skill-row span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.func-panel{height:100%}.panel-split{display:flex;height:100%}
.panel-left{width:260px;min-width:260px;padding:16px;border-right:1px solid #e5e7eb;overflow-y:auto;background:#fafafa}
.panel-title{font-size:13px;font-weight:600;color:#374151;margin-bottom:8px}
.panel-right{flex:1;overflow:hidden;display:flex;flex-direction:column}
.result-box{flex:1;overflow-y:auto;padding:16px 20px}
.result-text{font-size:13px;line-height:1.8;color:#1f2937}
.result-text :deep(h1),.result-text :deep(h2),.result-text :deep(h3){margin:8px 0 4px;font-size:15px}
.result-text :deep(p){margin:4px 0}.result-text :deep(ul),.result-text :deep(ol){margin:4px 0;padding-left:18px}
.result-text :deep(pre){background:#1e293b;color:#e2e8f0;padding:6px 10px;border-radius:6px;overflow-x:auto;font-size:12px}
.result-text :deep(code){background:#e5e7eb;padding:1px 3px;border-radius:3px;font-size:12px}
.empty{text-align:center;padding:60px;color:#bbb}
.write-task{display:flex;align-items:center;gap:6px;padding:7px 10px;border-radius:6px;cursor:pointer;font-size:12px;color:#374151;margin-bottom:3px}
.write-task:hover{background:#e8ecf1}.write-task.active{background:#1677ff12;color:#1677ff;font-weight:600}
@media(max-width:768px){.panel-split{flex-direction:column}.panel-left{width:100%;border-right:0;border-bottom:1px solid #e5e7eb}.chat-side,.chat-skill{display:none}}
</style>
