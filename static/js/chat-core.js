/**
 * CSIC AI Platform — Chat Core v5
 * 最新模型: 千问3.7 · 智谱5.2 · Kimi K2.7 · MiniMax · DeepSeek V4 Pro · 豆包
 * 最多 6 模型并行输出
 */

const MODEL_LABELS = {
    'qwen-max': '千问 3.7 Max',
    'glm-4': '智谱 GLM-5.2',
    'moonshot-v1': 'Kimi K2.7',
    'abab6.5': 'MiniMax abab6.5',
    'deepseek-chat': 'DeepSeek V4 Pro',
    'doubao-pro': '豆包 Pro',
};

const MODEL_CLASSES = {
    'qwen-max': 'qwen',
    'glm-4': 'zhipu',
    'moonshot-v1': 'kimi',
    'abab6.5': 'minimax',
    'deepseek-chat': 'deepseek',
    'doubao-pro': 'doubao',
};

const DEMO = {
    'qwen-max': '作为<strong>千问 3.7 Max</strong>，我从以下几个方面来分析：\n\n<strong>核心观点</strong>\n新时代背景下，国企党建工作面临新的机遇与挑战，需要理论与实践相结合。\n\n<strong>三个维度</strong>\n\n1. <strong>理论指导</strong>：习近平新时代中国特色社会主义思想为国企党建提供了根本遵循。\n\n2. <strong>实践路径</strong>：基层党组织建设需要通过规范化、制度化的机制来保障落实。\n\n3. <strong>创新驱动</strong>：数字化转型为党建工作提供了新的载体和工具。\n\n<strong>总结</strong>\n国企党建工作要做到理论指导与基层实践相统一，传统方法与数字创新相结合。',

    'glm-4': '作为<strong>智谱 GLM-5.2</strong>，我的分析视角如下：\n\n<strong>问题本质</strong>\n国企党建的核心在于将党的政治优势转化为企业的竞争优势。\n\n<strong>关键机制</strong>\n\n- <strong>组织嵌入</strong>：党的组织体系嵌入公司治理结构\n- <strong>文化引领</strong>：党的价值观塑造企业文化\n- <strong>人才保障</strong>：党管干部原则确保人才质量\n\n<strong>实践建议</strong>\n1. 完善"双向进入、交叉任职"领导体制\n2. 建立党建工作与经营业绩联动考核机制\n3. 发挥党员在技术创新中的先锋模范作用',

    'moonshot-v1': '作为<strong>Kimi K2.7</strong>，我提供以下分析：\n\n<strong>背景理解</strong>\n船舶行业具有资金密集、技术密集、劳动密集的特点，这决定了其党建工作必须紧密结合行业特性。\n\n<strong>行业特殊性分析</strong>\n\n1. <strong>安全要求高</strong>：军工背景决定了党建在保密、质量、安全方面的特殊地位\n2. <strong>人才结构多元</strong>：从高端科研到一线技工，党建需要分层分类施策\n3. <strong>项目制运作</strong>：大型船舶建造周期长，党建需要贯穿项目全生命周期',

    'abab6.5': '作为<strong>MiniMax abab6.5</strong>，我的思考如下：\n\n<strong>核心洞察</strong>\n党建不是负担，而是企业发展的"根"和"魂"。\n\n<strong>价值主张</strong>\n\n✨ <strong>战略层面</strong>：党组织"把方向、管大局、保落实"\n✨ <strong>管理层面</strong>：党建与业务"同部署、同落实、同考核"\n✨ <strong>文化层面</strong>：红色基因与企业精神深度融合\n\n<strong>最佳实践</strong>\n\n- 建立"党建+"工作机制：党建+安全生产、党建+技术创新\n- 打造"党员先锋岗"品牌，发挥示范引领作用',

    'deepseek-chat': '作为<strong>DeepSeek V4 Pro</strong>，我从深度推理角度给出分析：\n\n<strong>问题解构</strong>\n国企党建的本质是政治逻辑与经济逻辑的统一。\n\n<strong>一、制度层面</strong>\n中国特色社会主义现代企业制度的独特之处，在于将党的领导嵌入公司治理。这不仅是政治要求，更是提升决策质量的有效机制。\n\n<strong>二、组织层面</strong>\n基层组织是党建的神经末梢。数据显示，党建考核与经营业绩正相关的企业满意度高出32%。\n\n<strong>三、方法层面</strong>\n建议采用KPI+OKR双轨制考核，既保底线又促创新。',

    'doubao-pro': '作为<strong>豆包 Pro</strong>，我的分析如下：\n\n<strong>整体视角</strong>\n国企党建工作是一项系统工程，需要从战略高度进行顶层设计。\n\n<strong>关键抓手</strong>\n\n1. <strong>制度建设</strong>：将党建要求写入公司章程，明确党组织在公司治理中的法定地位\n2. <strong>队伍建设</strong>：培养既懂党务又懂业务的复合型人才\n3. <strong>平台建设</strong>：利用数字化手段提升党建工作的覆盖面和有效性\n\n<strong>总结</strong>\n党建工作与企业发展是相辅相成的关系，抓好了党建就是抓住了企业发展的"牛鼻子"。',
};

function chatApp(){return{
    chatMode:'single',
    selectedModel:'qwen-max',
    multiModels:['qwen-max','deepseek-chat','glm-4'],
    conversations:[],currentConvId:null,messages:[],input:'',isStreaming:!1,streamingContent:'',

    init(){this.newConversation()},
    newConversation(){const c={id:Date.now(),title:'新对话 '+(this.conversations.length+1)};this.conversations.unshift(c);this.currentConvId=c.id;this.messages=[];this.isStreaming=!1;this.$nextTick(()=>this.focus());},
    switchConversation(id){this.currentConvId=id;this.messages=[];this.isStreaming=!1;},
    switchMode(m){this.chatMode=m;if(m==='single'&&!this.selectedModel)this.selectedModel='qwen-max';if(m==='multi'&&this.multiModels.length===0)this.multiModels=['qwen-max','deepseek-chat','glm-4'];},

    send(){
        const c=this.input.trim();if(!c||this.isStreaming)return;
        if(this.chatMode==='multi'&&this.multiModels.length===0){alert('请至少选择一个模型');return;}
        if(this.chatMode==='multi'&&this.multiModels.length>6){alert('最多支持6个模型同时输出');return;}
        this.messages.push({role:'user',content:c,time:new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})});
        this.input='';this.scroll();this.isStreaming=!0;
        if(this.chatMode==='single')this._single(c);else this._multi(c);
    },

    _single(c){const m=this.selectedModel,r=DEMO[m]||'模拟回复';this.streamingContent='';let i=0;const t=setInterval(()=>{if(i<r.length){this.streamingContent+=r[i];i++;this.scroll();}else{clearInterval(t);this.messages.push({role:'assistant',model:m,content:r,time:new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})});this.streamingContent='';this.isStreaming=!1;this._title();}},12);},

    _multi(c){const ms=this.multiModels,mm={role:'assistant',models:ms.map(m=>({model:m,content:'',streaming:!0})),activeTab:0};this.messages.push(mm);let done=0;const speeds={'qwen-max':20,'glm-4':22,'moonshot-v1':18,'abab6.5':16,'deepseek-chat':24,'doubao-pro':19};ms.forEach((m,mi)=>{const r=DEMO[m]||'模拟回复';let i=0;const t=setInterval(()=>{if(i<r.length){mm.models[mi].content+=r[i];i++;this.scroll();}else{clearInterval(t);mm.models[mi].streaming=!1;done++;if(done===ms.length){this.isStreaming=!1;this._title();}}},speeds[m]||20);});},

    onKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();this.send();}},
    autoResize(e){const el=e.target;el.style.height='auto';el.style.height=Math.min(el.scrollHeight,140)+'px';},
    focus(){this.$nextTick(()=>{const el=this.$refs.inputEl;if(el)el.focus();});},
    scroll(){this.$nextTick(()=>{const c=this.$refs.msgContainer;if(c)c.scrollTop=c.scrollHeight;});},
    renderMd(t){if(!t)return'';try{return marked.parse(t);}catch(e){return t.replace(/\n/g,'<br>');}},
    getModelLabel(m){return MODEL_LABELS[m]||m;},
    getModelClass(m){return MODEL_CLASSES[m]||'';},
    _title(){if(this.conversations.length>0&&this.messages.length>0){const f=this.messages.find(m=>m.role==='user');if(f){const t=f.content.substring(0,28)+(f.content.length>28?'...':'');const c=this.conversations.find(c=>c.id===this.currentConvId);if(c&&c.title.startsWith('新对话'))c.title=t;}}}
};}
