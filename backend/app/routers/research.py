"""科研工作台路由 — AMiner + 科创助手 能力映射 gpt_academic"""

import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from ..auth import get_current_user

router = APIRouter(prefix="/api/research", tags=["科研"])

class ResearchQuery(BaseModel):
    query: str
    model: str = "deepseek"
    function: Optional[str] = None

async def _ai_stream(prompt: str, model: str = "deepseek"):
    """SSE 流式调用 DeepSeek"""
    import httpx
    from ..config import get_api_config
    key = get_api_config(model)
    if not key:
        yield f"data: {json.dumps({'content':f'[请先配置 {model} API Key]'})}\n\n"
        yield "data: [DONE]\n\n"; return
    
    async with httpx.AsyncClient(timeout=120) as c:
        async with c.stream("POST", "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model":"deepseek-chat","messages":[{"role":"user","content":prompt}],"temperature":0.7,"stream":True}
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    d = line[6:]
                    if d == "[DONE]": break
                    try:
                        chunk = json.loads(d)
                        c = chunk["choices"][0]["delta"].get("content","")
                        if c: yield f"data: {json.dumps({'content':c})}\n\n"
                    except: pass
    yield "data: [DONE]\n\n"

# ====== 学术搜索 — 真实 AMiner API 优先 ======
@router.post("/search")
async def academic_search(query: str = Form(...), model: str = Form("deepseek"), current_user: dict = Depends(get_current_user)):
    """AMiner 优先 — 真实 API + AI 增强"""
    
    # 尝试 AMiner API
    try:
        from ..services.aminer_service import comprehensive_search
        aminer_results = comprehensive_search(query, search_type="all", size=5)
        
        # 如果有真实结果，返回结构化数据
        has_data = any(
            (not isinstance(v, dict)) or (not v.get("error")) 
            for v in aminer_results.values()
        )
        if has_data:
            return {"source": "aminer", "data": aminer_results, "query": query}
    except Exception:
        pass
    
    # Fallback: AI 增强搜索
    prompt = f"""你是学术搜索专家。请搜索并分析以下研究课题，提供：
1. **研究概况** - 该领域当前研究热点和趋势（2-3段）
2. **关键文献** - 5篇该领域重要的代表性论文（标题、作者、年份、核心贡献）
3. **主要学者** - 3-5位该领域的知名学者及其研究方向
4. **推荐关键词** - 5个进一步检索的关键词
5. **研究方向建议** - 2-3个有潜力的研究方向

搜索主题：{query}"""
    return StreamingResponse(_ai_stream(prompt, model), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ====== 论文快速阅读 ======
@router.post("/paper-read")
async def paper_read(query: str = Form(...), model: str = Form("deepseek"), current_user: dict = Depends(get_current_user)):
    """AMiner AI阅读风格：深度解读论文"""
    prompt = f"""你是学术论文审读专家。请对以下论文内容进行结构化解读：

{query[:6000]}

请按以下格式输出：
1. **一句话概括** - 用一句话说明这篇论文做了什么
2. **研究背景与动机** - 为什么做这个研究
3. **核心贡献** - 主要创新点（3个）
4. **研究方法** - 技术路线简述
5. **实验与结果** - 关键发现
6. **局限性** - 作者提到的不足
7. **未来方向** - 可继续深入的方向"""
    return StreamingResponse(_ai_stream(prompt, model), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ====== 论文评审 ======
@router.post("/paper-review")
async def paper_review(query: str = Form(...), model: str = Form("deepseek"), current_user: dict = Depends(get_current_user)):
    """模拟学术审稿人评审论文"""
    prompt = f"""你是资深学术审稿人。请对以下论文进行评审：

{query[:5000]}

请从以下维度评审：
1. **总体评价** - 接收/修改后接收/拒稿，并说明理由
2. **创新性** - 评分(1-10)及评价
3. **方法严谨性** - 评价实验设计和数据分析
4. **写作质量** - 结构和表达评价
5. **具体修改建议** - 5条具体修改意见
6. **是否推荐引用** - 推荐引用的相关论文"""
    return StreamingResponse(_ai_stream(prompt, model), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ====== 一键范文生成 ======
@router.post("/generate-paper")
async def generate_paper(topic: str = Form(...), model: str = Form("deepseek"), current_user: dict = Depends(get_current_user)):
    """科创助手风格：一键生成万字论文初稿"""
    prompt = f"""请为课题「{topic}」撰写一篇规范的学术论文初稿。按以下结构：

**摘要** - 200字
**1. 引言** - 研究背景、问题陈述、研究意义
**2. 文献综述** - 国内外研究现状（分类梳理）
**3. 研究方法** - 技术路线、模型设计、实验方案
**4. 实验与分析** - 实验设置、结果展示、对比分析
**5. 结论与展望** - 总结贡献、局限性和未来方向
**参考文献** - 8篇格式规范的参考文献

请用学术语言，逻辑严谨，每个章节不少于500字。"""
    return StreamingResponse(_ai_stream(prompt, model), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ====== 技术趋势分析 ======
@router.post("/trend-analysis")
async def trend_analysis(field: str = Form(...), model: str = Form("deepseek"), current_user: dict = Depends(get_current_user)):
    """AMiner风格：技术发展趋势分析"""
    prompt = f"""你是科技情报分析专家。请分析「{field}」领域的技术发展趋势：

1. **发展历程** - 该领域近5年的发展脉络
2. **当前热点** - 3-5个当前最活跃的研究主题
3. **关键技术** - 该领域的核心技术和方法
4. **主要玩家** - 学术界(3个团队)和产业界(3个企业)的代表
5. **未来预测** - 未来3-5年的发展方向
6. **投资热点** - 哪些方向最受关注

请提供具体数据和趋势判断。"""
    return StreamingResponse(_ai_stream(prompt, model), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ====== PDF上传分析 ======
@router.post("/upload-paper")
async def upload_paper(file: UploadFile = File(...), func: str = Form("read"), current_user: dict = Depends(get_current_user)):
    """上传PDF并分析"""
    content = await file.read()
    text = f"[文件: {file.filename}]\n"
    try:
        import io; from PyPDF2 import PdfReader
        pdf = PdfReader(io.BytesIO(content))
        for page in pdf.pages[:8]: t = page.extract_text(); text += (t or "") + "\n"
    except: text += "[PDF解析失败，请检查文件]"
    
    prompt_map = {
        "read": f'你是学术审读专家。请深度解读以下论文，按「研究背景-核心贡献-研究方法-主要发现-局限性」5个维度分析：\n\n{text[:8000]}',
        "review": f'你是审稿人。请对以下论文进行学术评审（创新性/方法/写作/修改建议）：\n\n{text[:6000]}',
        "summary": f'请用300字总结以下论文的核心内容：\n\n{text[:5000]}',
        "translate": f"请将以下论文翻译为中文，保持学术风格：\n\n{text[:5000]}",
    }
    return StreamingResponse(_ai_stream(prompt_map.get(func, prompt_map["read"])), 
        media_type="text/event-stream", headers={"Cache-Control":"no-cache"})

# ====== Arxiv ======
@router.post("/arxiv")
async def arxiv_paper(url: str = Form(...), model: str = Form("deepseek"), current_user: dict = Depends(get_current_user)):
    import httpx, xml.etree.ElementTree as ET
    arxiv_id = url.split("/")[-1].replace("v1","").replace("v2","")
    async with httpx.AsyncClient() as c:
        resp = await c.get(f"http://export.arxiv.org/api/query?id_list={arxiv_id}")
        root = ET.fromstring(resp.text)
        ns = {"atom":"http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        title = entry.find("atom:title", ns).text.strip() if entry is not None else "未知"
        summary = entry.find("atom:summary", ns).text.strip()[:3000] if entry is not None else ""
    prompt = f"请解读这篇Arxiv论文：\n标题：{title}\n摘要：{summary}\n\n输出：1.中文标题 2.一句话概括 3.核心贡献(3点) 4.方法概述 5.结论"
    return StreamingResponse(_ai_stream(prompt, model), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ====== 通用SSE流式 ======
@router.post("/stream")
async def research_stream(req: ResearchQuery, current_user: dict = Depends(get_current_user)):
    func_map = {
        "paper_read": f"你是学术审读专家。请深度解读以下论文（研究背景-核心贡献-方法-发现-局限）：\n\n{req.query[:6000]}",
        "translate": f"你是专业学术翻译。请将以下内容翻译为中文，保持学术风格：\n\n{req.query[:6000]}",
        "polish": f"你是学术写作润色专家。请润色以下内容，优化表达和语法：\n\n{req.query[:5000]}",
        "outline": f"请为课题「{req.query}」生成完整学术论文大纲（选题背景-文献综述-目标-方法-创新-进度）",
        "review": f"请为主题「{req.query}」撰写文献综述（背景-现状-空白-方向）",
        "topics": f"请为研究方向「{req.query}」生成4个学术选题（含题目、创新点、可行性），返回JSON",
        "evaluate": f"请四维度（学术价值/创新性/可行性/应用价值）评估选题「{req.query}」",
        "literature": f"请搜索分析「{req.query}」领域文献（概况-关键论文-学者-关键词-建议）",
    }
    prompt = func_map.get(req.function, req.query)
    return StreamingResponse(_ai_stream(prompt, req.model), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
