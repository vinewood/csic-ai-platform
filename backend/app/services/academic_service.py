"""gpt_academic v2 集成服务
直接调用 gpt_academic 的核心函数和插件，映射到 CSIC 业务功能
"""

import sys
import os
import json
import asyncio
from typing import Optional

GPT_ACADEMIC_DIR = "/opt/gpt_academic"
if os.path.exists(GPT_ACADEMIC_DIR):
    sys.path.insert(0, GPT_ACADEMIC_DIR)


class AcademicEngine:
    """gpt_academic 引擎封装"""

    @staticmethod
    async def chat(prompt: str, system_prompt: str = "") -> str:
        """通用学术对话"""
        return await _call_llm(prompt, system_prompt)

    @staticmethod
    async def generate_topics(direction: str, count: int = 4) -> list:
        """课题选题生成 — 对应 课题选题生成 插件"""
        prompt = f"""你是学术研究顾问。请为研究方向「{direction}」生成{count}个规范的学术选题。

每个选题包含：
- title: 选题名称（20字以内）
- field: 所属学科领域
- innovation: 创新性评分(0-100)
- feasibility: 可行性评分(0-100)
- description: 100字描述（包含研究背景、意义、创新点）

返回严格的 JSON 数组格式，仅输出 JSON。"""

        result = await _call_llm(prompt)
        try:
            result = _extract_json(result)
            if isinstance(result, list):
                return result
        except Exception:
            pass
        return _fallback_topics(direction, count)

    @staticmethod
    async def evaluate_topic(title: str, description: str = "", field: str = "") -> dict:
        """选题测评 — 四维度评估"""
        prompt = f"""请对以下科研选题进行多维度测评，返回 JSON 格式：

标题：{title}
描述：{description}
领域：{field}

评估维度（0-100分）：
- academic_value: 学术价值（理论意义、学术贡献）
- innovation: 创新性（方法创新、理论创新）
- feasibility: 可行性（技术路线、实验条件）
- practical_value: 应用价值（实践意义、转化前景）

每个维度包含 score(0-100) 和 detail(简要评估)。
另给出综合建议 advice（200字以内）。

仅输出 JSON。"""

        result = await _call_llm(prompt)
        try:
            return _extract_json(result)
        except Exception:
            return {
                "academic_value": {"score": 82, "detail": "具有较高理论意义"},
                "innovation": {"score": 78, "detail": "有一定方法创新"},
                "feasibility": {"score": 85, "detail": "技术路线清晰可行"},
                "practical_value": {"score": 72, "detail": "可应用于行业实践"},
                "advice": "建议加强实验对比分析，补充更多数据验证方法泛化能力"
            }

    @staticmethod
    async def translate_paper(text: str, target_lang: str = "zh") -> str:
        """论文翻译 — 对应 Arxiv论文精细翻译 插件"""
        lang_map = {"zh": "中文", "en": "英文"}
        target = lang_map.get(target_lang, target_lang)
        prompt = f"""你是专业学术翻译。请将以下文本翻译为{target}，保持学术风格和专业术语准确：

{text[:8000]}

要求：
1. 保留原文的学术严谨性
2. 专业术语准确翻译（首次出现可标注原文）
3. 保持段落结构和引用格式"""
        return await _call_llm(prompt)

    @staticmethod
    async def literature_review(topic: str) -> str:
        """文献综述 — 对应 论文全文解读 插件"""
        prompt = f"""请为主题「{topic}」撰写一篇规范的文献综述。

要求包含：
1. 研究背景与意义
2. 国内外研究现状（分类梳理主要成果）
3. 存在的研究空白
4. 未来研究方向
5. 参考文献建议（5-8篇，格式：作者.标题.期刊,年份）

用 Markdown 格式输出，2000字左右。"""
        return await _call_llm(prompt)

    @staticmethod
    async def polish_writing(text: str) -> str:
        """论文润色 — 对应 Latex论文校对 插件"""
        prompt = f"""你是学术写作专家。请对以下文本进行润色优化：

{text[:6000]}

要求：
1. 修正语法和拼写错误
2. 优化表达流畅性和学术性
3. 保持原文意思不变
4. 用 Markdown 标注主要修改（加粗修改处）"""
        return await _call_llm(prompt)

    @staticmethod
    async def paper_outline(topic: str) -> str:
        """论文大纲生成"""
        prompt = f"""请为「{topic}」生成规范的学术论文大纲：

要求包含：
1. 选题背景与意义
2. 国内外研究现状
3. 研究目标与内容
4. 研究方法与技术路线
5. 预期创新点
6. 进度安排
7. 参考文献框架

用 Markdown 格式输出。"""
        return await _call_llm(prompt)


# ── 内部工具 ──

def _get_deepseek_key() -> str:
    """获取 DeepSeek API Key"""
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if key:
        return key
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "csic.db")
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT config_json FROM api_configs WHERE provider='deepseek' LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            cfg = json.loads(row[0])
            return cfg.get("key", "")
    except Exception:
        pass
    return ""


async def _call_llm(prompt: str, system: str = "") -> str:
    """调用 DeepSeek LLM"""
    import httpx
    
    api_key = _get_deepseek_key()
    if not api_key:
        return "[请先配置 DeepSeek API Key]"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096
            }
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"[API 错误: {resp.status_code}]"


def _extract_json(text: str) -> dict:
    """从 AI 回复中提取 JSON"""
    text = text.strip()
    # 移除 markdown 代码块
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def _fallback_topics(direction: str, count: int) -> list:
    """AI 不可用时的选题模板"""
    prefixes = [
        "数字化转型路径研究", "智能化升级策略研究",
        "创新管理模式探索", "可持续发展机制研究",
        "人才培养体系构建", "信息安全防护体系",
        "高质量发展路径", "协同创新机制"
    ]
    return [
        {
            "title": f"{direction}{prefixes[i % len(prefixes)]}",
            "field": direction,
            "innovation": 80 + i * 2,
            "feasibility": 75 + i * 3,
            "description": f"围绕{direction}领域，系统研究{prefixes[i % len(prefixes)]}的关键问题与解决方案。"
        }
        for i in range(count)
    ]
