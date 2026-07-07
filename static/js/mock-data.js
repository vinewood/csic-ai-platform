/**
 * CSIC AI Platform — Mock Data & API Simulation
 * 零后端完整交互: 所有 CRUD 操作存储在 localStorage，模拟网络延迟
 */

window.MOCK = window.MOCK || {};

// ── 模拟网络延迟 ──
function delay(ms) { return new Promise(r => setTimeout(r, ms || 300 + Math.random() * 400)); }

function randId() { return Math.random().toString(36).substr(2, 9); }

// ── 初始数据种子 ──
function initData() {
    if (localStorage.getItem('csic_mock_inited')) return;
    const data = {
        users: [
            { id: 'u1', name: '张讲师', username: 'zhangjs', role: '讲师', dept: '党建教研部', avatar: '张', email: 'zhang@csic.cn', defaultWs: 'teaching', active: true, lastLogin: '2026-07-04 14:30' },
            { id: 'u2', name: '李研究员', username: 'liyj', role: '研究员', dept: '船舶研究所', avatar: '李', email: 'li@csic.cn', defaultWs: 'research', active: true, lastLogin: '2026-07-04 10:15' },
            { id: 'u3', name: '王局长', username: 'wangld', role: '领导', dept: '校领导', avatar: '王', email: 'wang@csic.cn', defaultWs: 'news', active: true, lastLogin: '2026-07-03 16:00' },
            { id: 'u4', name: '赵管理', username: 'admin', role: '管理员', dept: '信息中心', avatar: '赵', email: 'admin@csic.cn', defaultWs: 'admin', active: true, lastLogin: '2026-07-04 15:00' },
            { id: 'u5', name: '陈教授', username: 'chenjs', role: '讲师', dept: '思政教研部', avatar: '陈', email: 'chen@csic.cn', defaultWs: 'teaching', active: true, lastLogin: '2026-07-04 09:20' },
            { id: 'u6', name: '高研究员', username: 'gaoyj', role: '研究员', dept: '政策研究室', avatar: '高', email: 'gao@csic.cn', defaultWs: 'research', active: false, lastLogin: '2026-07-02 11:00' },
        ],
        courses: [
            { id: 'c1', title: '习近平新时代中国特色社会主义思想解读', category: 'course', desc: '系统讲解新时代党的指导思想核心要义', slides: 12, status: 'published', views: 342, updatedAt: '2026-07-03', author: '张讲师' },
            { id: 'c2', title: '国有企业改革与党建创新', category: 'course', desc: '国有企业党建工作实践与制度创新', slides: 8, status: 'published', views: 218, updatedAt: '2026-07-02', author: '陈教授' },
            { id: 'c3', title: '船舶工业发展史', category: 'slide', desc: '从江南造船厂到三大造船基地', slides: 15, status: 'published', views: 156, updatedAt: '2026-07-01', author: '张讲师' },
            { id: 'c4', title: '党的二十大精神学习辅导', category: 'video', desc: '党的二十大精神核心内容视频课程', slides: 6, status: 'published', views: 489, updatedAt: '2026-07-03', author: '王局长' },
            { id: 'c5', title: '领导力与团队管理', category: 'course', desc: '企业中高层管理能力提升课程', slides: 10, status: 'draft', views: 0, updatedAt: '2026-07-04', author: '陈教授' },
            { id: 'c6', title: '大国重器：中国船舶集团创新之路', category: 'video', desc: 'CSSC科技创新成果纪录片', slides: 4, status: 'published', views: 267, updatedAt: '2026-06-30', author: '张讲师' },
            { id: 'c7', title: '国企党建案例汇编', category: 'case', desc: '全国国企党建优秀案例精选', slides: 20, status: 'published', views: 134, updatedAt: '2026-06-28', author: '李研究员' },
            { id: 'c8', title: '国际战略形势与国家安全', category: 'course', desc: '当前国际局势分析与国家安全战略', slides: 9, status: 'published', views: 198, updatedAt: '2026-06-25', author: '王局长' },
            { id: 'c9', title: '数字化转型下的企业培训新模式', category: 'slide', desc: 'AI赋能企业培训的创新实践', slides: 7, status: 'draft', views: 0, updatedAt: '2026-07-04', author: '赵管理' },
            { id: 'c10', title: '党纪学习教育专题', category: 'course', desc: '新修订纪律处分条例解读与案例警示', slides: 14, status: 'published', views: 376, updatedAt: '2026-06-20', author: '陈教授' },
        ],
        conversations: [
            { id: 'conv1', userId: 'u1', title: '国企党建研究', model: 'qwen-max', messages: 8, updatedAt: '2026-07-04 14:30', starred: true },
            { id: 'conv2', userId: 'u1', title: '课程大纲设计', model: 'deepseek-chat', messages: 12, updatedAt: '2026-07-04 10:00', starred: false },
            { id: 'conv3', userId: 'u2', title: '论文选题建议', model: 'glm-5.2', messages: 6, updatedAt: '2026-07-03 16:20', starred: true },
            { id: 'conv4', userId: 'u2', title: '文献综述生成', model: 'kimi-k2.7', messages: 15, updatedAt: '2026-07-03 11:00', starred: false },
            { id: 'conv5', userId: 'u3', title: '新闻摘要日报', model: 'qwen-max', messages: 4, updatedAt: '2026-07-04 08:00', starred: true },
            { id: 'conv6', userId: 'u4', title: '系统配置测试', model: 'doubao-pro', messages: 3, updatedAt: '2026-07-04 09:00', starred: false },
        ],
        messages: [
            { id: 'm1', convId: 'conv1', role: 'user', content: '请介绍一下国企党建的最新政策要求', createdAt: '2026-07-04 14:30' },
            { id: 'm2', convId: 'conv1', role: 'assistant', model: 'qwen-max', content: '根据最新政策文件，国企党建工作需要重点把握以下方向：\n\n1. **坚持和加强党对国有企业的全面领导**\n2. **推进党建工作与生产经营深度融合**\n3. **完善中国特色现代企业制度**\n4. **强化国有企业基层党组织建设**\n\n具体而言，2024年以来中央出台了多项关于国企党建的重要文件，强调把加强党的领导和完善公司治理统一起来...', createdAt: '2026-07-04 14:31' },
            { id: 'm3', convId: 'conv3', role: 'user', content: '帮我生成几个船舶工业数字化转型的研究选题', createdAt: '2026-07-03 16:20' },
            { id: 'm4', convId: 'conv3', role: 'assistant', model: 'glm-5.2', content: '以下是一些船舶工业数字化转型的研究选题建议：\n\n1. **数字孪生技术在船舶设计建造中的应用研究**\n2. **基于工业互联网的船舶供应链协同机制**\n3. **AI驱动的船舶智能运维决策系统研究**\n4. **船舶制造过程的数字化质量管控体系**\n5. **区块链技术在船舶供应链金融中的应用探索**', createdAt: '2026-07-03 16:21' },
        ],
        rssSources: [
            { id: 's1', name: '新华网', route: 'xinhua/news', category: '时政', interval: 30, active: true, lastFetch: '2026-07-04 14:00' },
            { id: 's2', name: '人民网', route: 'people/news', category: '时政', interval: 30, active: true, lastFetch: '2026-07-04 14:00' },
            { id: 's3', name: '求是网', route: 'qstheory/news', category: '党建', interval: 60, active: true, lastFetch: '2026-07-04 13:00' },
            { id: 's4', name: '中国船舶报', route: 'csic/news', category: '船舶', interval: 60, active: true, lastFetch: '2026-07-04 12:00' },
            { id: 's5', name: '科技日报', route: 'stdaily/news', category: '科技', interval: 120, active: true, lastFetch: '2026-07-04 10:00' },
            { id: 's6', name: '经济日报', route: 'ce/news', category: '经济', interval: 120, active: true, lastFetch: '2026-07-04 10:00' },
            { id: 's7', name: '学习强国', route: 'xuexi/news', category: '党建', interval: 60, active: false, lastFetch: '2026-07-03 08:00' },
        ],
        news: [
            { id: 'n1', sourceId: 's1', title: '习近平：进一步全面深化改革 推进中国式现代化', url: '#', category: '时政', summary: '习近平总书记主持会议并发表重要讲话，强调要牢牢把握改革正确方向...', publishedAt: '2026-07-04 08:00', hot: true },
            { id: 'n2', sourceId: 's2', title: '全国国有企业党的建设工作会议精神落实取得新成效', url: '#', category: '党建', summary: '近年来，各中央企业持续深化国有企业党的建设，推动党建工作与生产经营深度融合...', publishedAt: '2026-07-04 07:30', hot: true },
            { id: 'n3', sourceId: 's3', title: '新时代国有企业党建与业务融合的创新路径', url: '#', category: '党建', summary: '新时代背景下，国有企业党建工作需要从制度建设、机制创新、文化引领等多维度推动与业务深度融合...', publishedAt: '2026-07-04 07:00', hot: false },
            { id: 'n4', sourceId: 's4', title: '中国船舶集团一季度造船完工量同比增长15%', url: '#', category: '船舶', summary: '中国船舶集团发布2026年第一季度报告，造船完工量同比增长15%，新接订单量同比增长22%...', publishedAt: '2026-07-04 06:30', hot: true },
            { id: 'n5', sourceId: 's5', title: 'AI大模型在工业制造领域的应用突破', url: '#', category: '科技', summary: '随着AI大模型技术的快速发展，工业制造领域正迎来新一轮智能化变革...', publishedAt: '2026-07-04 06:00', hot: false },
            { id: 'n6', sourceId: 's6', title: '我国船舶工业进出口贸易保持增长态势', url: '#', category: '经济', summary: '海关总署最新数据显示，我国船舶工业进出口贸易持续保持增长...', publishedAt: '2026-07-04 05:30', hot: false },
            { id: 'n7', sourceId: 's1', title: '中央企业数字化转型取得阶段性成果', url: '#', category: '时政', summary: '国务院国资委通报中央企业数字化转型工作进展情况...', publishedAt: '2026-07-03 16:00', hot: false },
            { id: 'n8', sourceId: 's2', title: '推动党纪学习教育走深走实', url: '#', category: '党建', summary: '各地各部门扎实推进党纪学习教育，引导党员干部学纪、知纪、明纪、守纪...', publishedAt: '2026-07-03 15:00', hot: false },
            { id: 'n9', sourceId: 's4', title: '国产首艘大型邮轮开启新航季', url: '#', category: '船舶', summary: '我国首艘国产大型邮轮正式开启2026年夏季运营航季...', publishedAt: '2026-07-03 14:00', hot: true },
            { id: 'n10', sourceId: 's5', title: '6G通信技术研发取得关键进展', url: '#', category: '科技', summary: '我国6G技术研发团队在太赫兹通信领域取得突破性进展...', publishedAt: '2026-07-03 10:00', hot: false },
            { id: 'n11', sourceId: 's6', title: '2026年上半年国民经济运行稳中有进', url: '#', category: '经济', summary: '国家统计局发布2026年上半年国民经济运行数据...', publishedAt: '2026-07-03 09:00', hot: true },
            { id: 'n12', sourceId: 's1', title: '共建"一带一路"取得新成果', url: '#', category: '时政', summary: '＂一带一路＂倡议提出以来，中国与沿线国家在基础设施、贸易投资等领域合作不断深化...', publishedAt: '2026-07-03 08:00', hot: false },
        ],
        dailyBriefs: [
            { id: 'db1', date: '2026-07-04', content: '【党建要闻】全国国企党建工作会议精神落实取得新成效；【船舶动态】中国船舶集团一季度造船完工量同比增长15%；【科技前沿】AI大模型在工业制造领域应用突破；【经济观察】我国船舶工业进出口贸易保持增长态势。', generatedAt: '2026-07-04 08:00' },
            { id: 'db2', date: '2026-07-03', content: '【时政要闻】习近平主持召开中央深改委会议；【党纪学习】推动党纪学习教育走深走实；【船舶动态】国产首艘大型邮轮开启新航季；【科技前沿】6G通信技术研发取得关键进展。', generatedAt: '2026-07-03 08:00' },
        ],
        skills: [
            { id: 'sk1', name: '课程大纲生成', category: '教学', desc: 'AI自动生成结构化课程大纲，涵盖教学目标、章节安排、考核方式', prompt: '请生成一份关于...的课程大纲', usage: 128, rating: 4.8, author: '张讲师', shared: true },
            { id: 'sk2', name: '论文选题分析', category: '科研', desc: '基于研究热点和趋势，推荐具有创新性的论文选题方向', prompt: '请分析...领域的最新研究热点', usage: 95, rating: 4.6, author: '李研究员', shared: true },
            { id: 'sk3', name: '文献摘要生成', category: '科研', desc: '快速提取论文核心观点、方法、结论，生成学术摘要', prompt: '请总结以下论文的核心观点...', usage: 213, rating: 4.9, author: '李研究员', shared: true },
            { id: 'sk4', name: '党建案例分析', category: '教学', desc: '深度分析国企党建典型案例，提炼经验做法和可推广模式', prompt: '请分析以下党建案例的关键要素...', usage: 76, rating: 4.5, author: '陈教授', shared: true },
            { id: 'sk5', name: '新闻摘要日报', category: '新闻', desc: '聚合当日新闻，自动生成分类摘要和要点简报', prompt: '请对以下新闻进行分类汇总...', usage: 342, rating: 4.7, author: '赵管理', shared: true },
            { id: 'sk6', name: '视频内容提炼', category: '工具', desc: '从视频转录文本中提取关键信息、生成思维导图', prompt: '请从以下视频转录内容中提取核心信息...', usage: 67, rating: 4.4, author: '赵管理', shared: true },
            { id: 'sk7', name: '试卷自动生成', category: '教学', desc: '根据课程内容自动生成选择题、填空题、简答题等', prompt: '请基于以下课程内容生成一套试卷...', usage: 54, rating: 4.3, author: '张讲师', shared: false },
            { id: 'sk8', name: '报告润色校对', category: '科研', desc: '对学术报告、论文进行语法检查、格式规范和学术润色', prompt: '请对以下报告进行专业润色...', usage: 189, rating: 4.8, author: '陈教授', shared: true },
            { id: 'sk9', name: '会议纪要整理', category: '工具', desc: '将会议录音文字整理为结构化会议纪要', prompt: '请将以下会议内容整理为纪要...', usage: 156, rating: 4.6, author: '王局长', shared: true },
            { id: 'sk10', name: '多模型对比分析', category: '工具', desc: '同时调用多个AI模型对同一问题进行回答，对比分析差异', prompt: '请从多个角度分析...', usage: 88, rating: 4.5, author: '赵管理', shared: true },
            { id: 'sk11', name: '企业制度合规审查', category: '科研', desc: '自动检测企业制度文件与最新法规政策的合规性', prompt: '请检查以下制度文件是否符合最新法规要求...', usage: 43, rating: 4.2, author: '高研究员', shared: false },
            { id: 'sk12', name: 'PPT内容生成', category: '教学', desc: '根据讲义内容生成PPT大纲和每页要点', prompt: '请根据以下内容生成PPT大纲...', usage: 112, rating: 4.4, author: '张讲师', shared: true },
        ],
        videos: [
            { id: 'v1', name: '党的二十大精神专题辅导报告.mp4', status: 'completed', duration: '01:25:30', size: '1.2GB', progress: 100, uploadedAt: '2026-07-03', transcript: true, summary: true, mindmap: true, notes: true },
            { id: 'v2', name: '国企党建工作经验交流会.mov', status: 'completed', duration: '02:10:00', size: '2.8GB', progress: 100, uploadedAt: '2026-07-02', transcript: true, summary: true, mindmap: true, notes: false },
            { id: 'v3', name: '船舶智能制造技术讲座.mp4', status: 'processing', duration: '00:45:00', size: '680MB', progress: 62, uploadedAt: '2026-07-04', transcript: false, summary: false, mindmap: false, notes: false },
        ],
        videoResults: {
            'v1': {
                transcript: '今天我们要深入学习党的二十大精神...（完整转录文本约3000字）\n\n党的二十大的主题是：高举中国特色社会主义伟大旗帜...\n\n中国式现代化是中国共产党领导的社会主义现代化...\n\n高质量发展是全面建设社会主义现代化国家的首要任务...',
                summary: '本次辅导报告围绕党的二十大精神核心内容展开，重点讲解了：\n1. 大会主题与历史方位\n2. 中国式现代化的内涵与路径\n3. 高质量发展战略部署\n4. 全面从严治党新要求',
                mindmap: { root: '二十大精神', children: [{ name: '大会主题', children: [{ name: '高举旗帜' }, { name: '伟大征程' }] }, { name: '中国式现代化', children: [{ name: '人口规模巨大' }, { name: '共同富裕' }, { name: '人与自然和谐' }] }, { name: '高质量发展', children: [{ name: '创新驱动' }, { name: '协调发展' }, { name: '绿色转型' }] }, { name: '党的建设', children: [{ name: '政治建设' }, { name: '思想建设' }, { name: '组织建设' }] }] },
                notes: '核心要点笔记：\n- 二十大是在关键时刻召开的重要会议\n- 中国式现代化五个特色\n- 高质量发展是首要任务\n- 全面从严治党永远在路上'
            },
            'v2': {
                transcript: '各位领导、同志们，今天我们召开国企党建工作经验交流会...（完整转录约5000字）',
                summary: '本次经验交流会总结了2026年上半年国企党建工作的主要成效：\n1. 党建工作与业务融合取得新突破\n2. 基层党组织标准化建设全面推进\n3. 党员先锋岗创建活动成效显著',
                mindmap: { root: '国企党建', children: [{ name: '融合突破', children: [{ name: '党建+经营' }, { name: '党建+创新' }] }, { name: '标准化建设', children: [{ name: '组织设置' }, { name: '制度建设' }, { name: '考核评价' }] }, { name: '先锋岗创建', children: [{ name: '示范引领' }, { name: '品牌打造' }] }] },
                notes: '交流要点：\n- 江南造船厂"党建+项目"模式\n- 沪东中华"党员创新工作室"\n- 外高桥造船"红色生产线"'
            }
        },
        projects: [
            { id: 'p1', userId: 'u2', name: '船舶工业数字化转型研究', desc: '研究数字孪生、AI在船舶设计建造中的应用', status: '进行中', members: 3, papers: 2, updatedAt: '2026-07-03' },
            { id: 'p2', userId: 'u2', name: '国企党建与公司治理融合研究', desc: '实证研究党组织嵌入公司治理的机制与效果', status: '进行中', members: 5, papers: 1, updatedAt: '2026-07-02' },
            { id: 'p3', userId: 'u1', name: 'AI辅助课程开发研究', desc: '探索大模型在党校课程开发中的应用方法', status: '立项', members: 2, papers: 0, updatedAt: '2026-07-01' },
        ],
        usage: [
            { id: 'u1', model: '千问 3.7 Max', calls: 2842, tokens: 1250000, cost: 12.50, users: 18 },
            { id: 'u2', model: '智谱 GLM-5.2', calls: 1634, tokens: 890000, cost: 8.90, users: 12 },
            { id: 'u3', model: 'DeepSeek V4 Pro', calls: 2156, tokens: 980000, cost: 4.90, users: 15 },
            { id: 'u4', model: 'Kimi K2.7', calls: 987, tokens: 520000, cost: 5.20, users: 8 },
            { id: 'u5', model: 'MiniMax abab6.5', calls: 542, tokens: 310000, cost: 3.10, users: 5 },
            { id: 'u6', model: '豆包 Pro', calls: 1245, tokens: 670000, cost: 3.35, users: 10 },
        ],
        models: [
            { id: 'qwen-max', name: '千问 3.7 Max', provider: '阿里云百炼', endpoint: 'dashscope.aliyuncs.com', enabled: true, order: 1 },
            { id: 'glm-5.2', name: '智谱 GLM-5.2', provider: '智谱 AI', endpoint: 'open.bigmodel.cn', enabled: true, order: 2 },
            { id: 'kimi-k2.7', name: 'Kimi K2.7', provider: 'Moonshot', endpoint: 'api.moonshot.cn', enabled: true, order: 3 },
            { id: 'minimax', name: 'MiniMax abab6.5', provider: 'MiniMax', endpoint: 'api.minimax.chat', enabled: true, order: 4 },
            { id: 'deepseek-chat', name: 'DeepSeek V4 Pro', provider: 'DeepSeek', endpoint: 'api.deepseek.com', enabled: true, order: 5 },
            { id: 'doubao-pro', name: '豆包 Pro', provider: '字节跳动', endpoint: 'ark.cn-beijing.volces.com', enabled: true, order: 6 },
        ],
        knowledgeBases: [
            { id: 'kb1', name: '党的二十大精神学习资料', type: '个人', owner: '张讲师', docs: 12, shared: false, createdAt: '2026-07-01', updatedAt: '2026-07-04' },
            { id: 'kb2', name: '国企党建政策文件库', type: '个人', owner: '李研究员', docs: 25, shared: true, createdAt: '2026-06-15', updatedAt: '2026-07-03' },
            { id: 'kb3', name: '船舶行业报告汇编', type: '组织', owner: '信息中心', docs: 48, shared: true, createdAt: '2026-05-01', updatedAt: '2026-07-04' },
            { id: 'kb4', name: '党校精品课程资料', type: '组织', owner: '教务部', docs: 36, shared: true, createdAt: '2026-04-10', updatedAt: '2026-07-02' },
            { id: 'kb5', name: 'AI技术学习笔记', type: '个人', owner: '赵管理', docs: 8, shared: false, createdAt: '2026-07-02', updatedAt: '2026-07-04' },
        ],
        documents: [
            { id: 'doc1', kbId: 'kb1', name: '二十大报告全文.pdf', type: 'pdf', size: '2.3MB', uploadedAt: '2026-07-01', status: 'indexed', chunks: 45 },
            { id: 'doc2', kbId: 'kb1', name: '二十大精神学习要点.docx', type: 'docx', size: '1.1MB', uploadedAt: '2026-07-02', status: 'indexed', chunks: 22 },
            { id: 'doc3', kbId: 'kb1', name: '党章修正案解读.pdf', type: 'pdf', size: '856KB', uploadedAt: '2026-07-03', status: 'indexed', chunks: 18 },
            { id: 'doc4', kbId: 'kb2', name: '国企基层组织工作条例.pdf', type: 'pdf', size: '1.5MB', uploadedAt: '2026-06-20', status: 'indexed', chunks: 30 },
            { id: 'doc5', kbId: 'kb2', name: '关于深化国企改革的指导意见.docx', type: 'docx', size: '980KB', uploadedAt: '2026-06-25', status: 'indexed', chunks: 20 },
            { id: 'doc6', kbId: 'kb3', name: '2026船舶工业发展白皮书.pdf', type: 'pdf', size: '5.2MB', uploadedAt: '2026-07-01', status: 'indexed', chunks: 80 },
            { id: 'doc7', kbId: 'kb5', name: 'LangChain入门指南.pdf', type: 'pdf', size: '2.1MB', uploadedAt: '2026-07-03', status: 'indexed', chunks: 35 },
        ],
        apiConfigs: {
            bailian: { key: 'sk-********', endpoint: 'dashscope.aliyuncs.com', enabled: true },
            zhipu: { key: '', endpoint: 'open.bigmodel.cn', enabled: false },
            kimi: { key: 'sk-test-key', endpoint: 'api.moonshot.cn', enabled: true },
            deepseek: { key: 'sk-ds-test', endpoint: 'api.deepseek.com', enabled: true },
            minimax: { key: '', endpoint: 'api.minimax.chat', enabled: false },
            doubao: { key: '', endpoint: 'ark.cn-beijing.volces.com', enabled: false },
            aminer: { key: '', endpoint: 'api.aminer.cn', enabled: false },
            cqvip: { key: '', endpoint: 'open.cqvip.com', enabled: false },
            gpt_academic: { key: '', endpoint: 'gpt-academic:8080', enabled: false },
            rsshub: { key: '', endpoint: 'rsshub:1200', enabled: true },
            miniflux: { key: 'mfx-token-001', endpoint: 'miniflux:8080', enabled: true },
            video_trans: { key: '', endpoint: 'video-trans:5000', enabled: false },
            oss: { key: '', endpoint: 'oss-cn-beijing.aliyuncs.com', enabled: false },
        },
        // 各模块统计
        stats: {
            totalUsers: 42,
            activeUsers: 38,
            totalCourses: 128,
            totalSkills: 24,
            totalVideos: 56,
            totalConversations: 1240,
            dailyMessages: 380,
            totalCost: 38.45,
        }
    };
    localStorage.setItem('csic_mock_data', JSON.stringify(data));
    localStorage.setItem('csic_mock_inited', '1');
}

// ── 读取/写入数据 ──
function getData() { return JSON.parse(localStorage.getItem('csic_mock_data') || '{}'); }
function saveData(d) { localStorage.setItem('csic_mock_data', JSON.stringify(d)); }

// ── 初始化 ──
initData();

// ── Mock API 函数 ──

/** 获取列表（支持分页和搜索） */
MOCK.list = async function(table, query = {}) {
    await delay();
    const data = getData();
    let items = data[table] || [];
    // 搜索
    if (query.search) {
        const q = query.search.toLowerCase();
        items = items.filter(i => JSON.stringify(i).toLowerCase().includes(q));
    }
    // 过滤
    if (query.filter) {
        Object.entries(query.filter).forEach(([k, v]) => {
            items = items.filter(i => i[k] === v);
        });
    }
    return { code: 0, data: items, total: items.length };
};

/** 获取单条 */
MOCK.get = async function(table, id) {
    await delay(150);
    const data = getData();
    const item = (data[table] || []).find(i => i.id === id);
    return { code: item ? 0 : 404, data: item || null };
};

/** 添加 */
MOCK.add = async function(table, item) {
    await delay(200);
    const data = getData();
    if (!data[table]) data[table] = [];
    const newItem = { ...item, id: randId(), createdAt: new Date().toISOString() };
    data[table].push(newItem);
    saveData(data);
    return { code: 0, data: newItem };
};

/** 更新 */
MOCK.update = async function(table, id, updates) {
    await delay(200);
    const data = getData();
    const items = data[table] || [];
    const idx = items.findIndex(i => i.id === id);
    if (idx === -1) return { code: 404 };
    items[idx] = { ...items[idx], ...updates };
    saveData(data);
    return { code: 0, data: items[idx] };
};

/** 删除 */
MOCK.del = async function(table, id) {
    await delay(200);
    const data = getData();
    data[table] = (data[table] || []).filter(i => i.id !== id);
    saveData(data);
    return { code: 0 };
};

/** 获取统计数据 */
MOCK.getStats = async function() {
    await delay(200);
    return { code: 0, data: getData().stats };
};

/** 模拟AI对话流式响应 */
MOCK.chatStream = function(messages, model, onChunk) {
    const responses = {
        'qwen-max': '从系统角度分析，国企党建工作需要把握三个核心维度：\n\n**一、政治引领**\n坚持党的领导是国企的"根"和"魂"。\n\n**二、组织建设**\n强化基层党组织战斗堡垒作用。\n\n**三、融合发展**\n推动党建与经营深度融合。',
        'glm-5.2': '我认为这个问题的关键在于如何将党的政治优势转化为企业治理效能。\n\n1. 完善"双向进入、交叉任职"领导体制\n2. 建立党建工作考核与经营业绩联动机制\n3. 发挥党员在技术创新中的先锋模范作用',
        'kimi-k2.7': '船舶行业具有资金密集、技术密集特点，其党建工作必须紧密结合行业特性。\n\n• **安全要求高**：军工背景决定党建在质量安全方面的特殊地位\n• **人才结构多元**：从科研到一线，党建需分层分类施策',
        'minimax': '核心洞察：党建不是负担，而是企业发展的"根"和"魂"。\n\n✨ **战略层面**：党组织"把方向、管大局、保落实"\n✨ **管理层面**：党建与业务"同部署、同落实、同考核"\n✨ **文化层面**：红色基因与企业精神深度融合',
        'deepseek-chat': '从深度推理角度分析：\n\n**问题解构**\n国企党建的本质是政治逻辑与经济逻辑的统一。\n\n**制度层面**\n党的领导嵌入公司治理不仅是政治要求，更是提升决策质量的机制。\n\n**数据支撑**\n党建考核与经营业绩正相关的企业满意度高出32%。',
        'doubao-pro': '国企党建工作是一项系统工程，需要从战略高度进行顶层设计。\n\n**关键抓手**\n1. 制度建设：将党建要求写入公司章程\n2. 队伍建设：培养又红又专的复合型人才\n3. 平台建设：利用数字化手段提升党建实效',
    };
    const text = responses[model] || responses['qwen-max'];
    let i = 0;
    function streamNext() {
        if (i < text.length) {
            const chunkSize = 3 + Math.floor(Math.random() * 5);
            const chunk = text.substring(i, Math.min(i + chunkSize, text.length));
            onChunk(chunk);
            i += chunkSize;
            const delay = 20 + Math.random() * 40;
            setTimeout(streamNext, delay);
        } else {
            onChunk(null); // done
        }
    }
    streamNext();
    return { abort: () => {} };
};

/** 多模型并行对话 */
MOCK.multiChatStream = function(messages, models, onChunks) {
    const aborts = [];
    models.forEach(model => {
        const ab = MOCK.chatStream(messages, model, (chunk) => {
            onChunks(model, chunk);
        });
        aborts.push(ab);
    });
    return { abort: () => aborts.forEach(a => a.abort()) };
};

/** 获取知识库列表 */
MOCK.listKnowledgeBases = async function(filter = {}) {
    await delay();
    const data = getData();
    let items = data.knowledgeBases || [];
    if (filter.type) items = items.filter(i => i.type === filter.type);
    if (filter.search) {
        const q = filter.search.toLowerCase();
        items = items.filter(i => i.name.toLowerCase().includes(q));
    }
    return { code: 0, data: items };
};

/** 获取某知识库的文档列表 */
MOCK.listDocuments = async function(kbId) {
    await delay();
    const data = getData();
    return { code: 0, data: (data.documents || []).filter(d => d.kbId === kbId) };
};

// ── 便捷访问 ──
MOCK.getData = getData;
MOCK.initData = initData;
