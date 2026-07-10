# AMiner 开放数据平台 — API 集成文档

> 智谱AI · AMiner · https://open.aminer.cn  
> 用户ID: `6a50f0d66368530ed6f3aef7`  
> API Key: `MTpI2JKWPNo1xQ==` (Base64, JWT HS256 签名密钥)  
> Base URL: `https://datacenter.aminer.cn/gateway/open_platform/api`  
> 更新日期: 2026-07-10

---

## 1. 认证方式 (JWT HS256)

```python
import jwt, time

API_KEY = "MTpI2JKWPNo1xQ=="
USER_ID = "6a50f0d66368530ed6f3aef7"

payload = {
    "user_id": USER_ID,
    "exp": int(time.time()) + 3600,      # 过期时间（Unix秒）
    "timestamp": int(time.time())         # 当前时间戳
}
headers_jwt = {"alg": "HS256", "sign_type": "SIGN"}
token = jwt.encode(payload, API_KEY, algorithm="HS256", headers=headers_jwt)

# HTTP 请求 Header
# Authorization: <token>
```

---

## 2. 论文搜索 API

### 2.1 多条件论文搜索 (GET) — 需充值余额
```
GET /paper/search/pro?page=0&size=10&title=关键词
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| page | number | 否 | 页数(从0开始) |
| size | number | 否 | 条数(最大100) |
| title | string | 否 | 论文标题关键词 |
| keyword | string | 否 | 关键词 |
| abstract | string | 否 | 摘要关键词 |
| author | string | 否 | 作者名 |
| org | string | 否 | 机构名 |
| venue | string | 否 | 期刊/会议 |
| order | string | 否 | 排序 `year`/`n_citation` (降序) |

### 2.2 AI 学术问答搜索 (POST)
```
POST /paper/qa/search
Content-Type: application/json;charset=utf-8
{
    "query": "自然语言问题",
    "size": 5,
    "use_topic": true,
    "topic_high": [["关键词组1"], ["关键词组2"]]
}
```

### 2.3 论文批量信息 (POST)
```
POST /paper/info
{ "ids": ["paper_id_1", "paper_id_2"] }
```

### 2.4 论文详情 (GET)
```
GET /paper/detail?id=<paper_id>
```

### 2.5 论文引用链 (GET)
```
GET /paper/relation?id=<paper_id>
```

---

## 3. 学者搜索 API ✅ 已验证

### 3.1 搜索学者 (POST) — ✅ 可用
```
POST /person/search
{ "name": "学者姓名", "size": 10 }
```

### 3.2 学者详情 (GET)
```
GET /person/detail?id=<scholar_id>
```

### 3.3 学者画像 (GET)
```
GET /person/figure?id=<scholar_id>
```

### 3.4 学者论文列表 (GET)
```
GET /person/paper_relation?id=<scholar_id>&size=10
```

### 3.5 学者专利列表 (GET)
```
GET /person/patent_relation?id=<scholar_id>
```

### 3.6 学者科研项目 (GET)
```
GET /person/project?id=<scholar_id>
```

---

## 4. 机构搜索 API

### 4.1 搜索机构 (POST)
```
POST /org/search
{ "name": "机构名称", "size": 10 }
```

### 4.2 机构详情 (POST)
```
POST /org/detail
{ "id": "<org_id>" }
```

### 4.3 机构消歧 (POST)
```
POST /org/disambiguate
{ "name": "可能重复的机构名" }
```

### 4.4 机构学者 (GET)
```
GET /org/person_relation?id=<org_id>
```

### 4.5 机构论文 (GET)
```
GET /org/paper_relation?id=<org_id>
```

---

## 5. 期刊 API

### 5.1 搜索期刊 (POST)
```
POST /venue/search
{ "name": "期刊名称", "size": 10 }
```

### 5.2 期刊详情 (POST)
```
POST /venue/detail
{ "id": "<venue_id>" }
```

### 5.3 期刊论文 (POST)
```
POST /venue/paper_relation
{ "id": "<venue_id>", "year": 2024 }
```

---

## 6. 专利 API

### 6.1 专利搜索 (POST)
```
POST /patent/search
{ "keyword": "关键词", "size": 10 }
```

### 6.2 专利基本信息 (GET)
```
GET /patent/info?id=<patent_id>
```

### 6.3 专利详情 (GET)
```
GET /patent/detail?id=<patent_id>
```

---

## 7. 五大工作流

### 工作流1: 学者画像
`person_search → person_detail → person_figure → person_paper_relation → person_patent_relation → person_project`

### 工作流2: 论文深挖
`paper_search → paper_detail → paper_relation → paper_info`

### 工作流3: 机构分析
`org_disambiguate_pro → org_detail → org_person_relation → org_paper_relation → org_patent_relation`

### 工作流4: 期刊论文
`venue_search → venue_detail → venue_paper_relation`

### 工作流5: 专利分析
`patent_search → patent_info/patent_detail`

---

## 8. 实体链接格式

| 实体 | URL |
|------|-----|
| 论文 | `https://www.aminer.cn/pub/{paper_id}` |
| 学者 | `https://www.aminer.cn/profile/{scholar_id}` |
| 专利 | `https://www.aminer.cn/patent/{patent_id}` |
| 期刊 | `https://www.aminer.cn/open/journal/detail/{journal_id}` |

---

## 9. 错误码

| 代码 | 说明 |
|:--:|------|
| 40001 | 参数错误 |
| 40301 | 权限禁用 |
| 40302 | Token过期 |
| 40306 | 访问频率过快 |
| 40307 | 无效的API Key |
| 40308 | 无效的Token |
| 50001 | 服务出错 |

---

## 10. 数据规模

| 类型 | 数量 |
|------|-----|
| 学者 | 6000万+ |
| 论文 | 3.3亿+ |
| 专利 | 1.8亿+ |
| 科研项目 | 500万+ |
| 新闻资讯 | 460万+ |

---

## 11. CSIC 集成文件

- `backend/app/services/aminer_service.py` — 完整封装（27个API + 综合检索）
- `backend/app/routers/research.py` — `/api/research/search` AMiner优先
- 数据库: `api_configs` 表 provider=`aminer`

### 当前限制
- 论文搜索需要余额充值（当前 0.00 元）
- 学者搜索完全免费可用
- 充值地址: https://open.aminer.cn → 控制台 → 账户充值
