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
            if isinstance(result, list) and len(result) > 0:
                return result
        except Exception:
            pass
        # 失败即明示：AI 不可用或返回格式异常时如实报错，禁止回退模板假数据
        raise RuntimeError("AI 选题生成失败或返回格式异常，请重试")

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
            # 失败即明示：绝不返回硬编码假评分冒充 AI 评估结果
            raise RuntimeError("AI 选题测评失败或返回格式异常，请重试")

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

async def _call_llm(prompt: str, system: str = "") -> str:
    """调用 DeepSeek LLM —— 统一从 api_configs 保险箱取 key，模型名用该账号真实可用的 deepseek-v4-pro

    修复历史 bug：旧实现用 sqlite 直读 DB + 模型名 deepseek-chat（该账号不存在此模型，必然 400）。
    失败即明示：抛 RuntimeError，由调用方决定如何呈现，禁止返回伪装内容。
    """
    import httpx
    from ..config import get_api_config

    api_key = get_api_config("deepseek")
    if not api_key:
        raise RuntimeError("未配置 DeepSeek API Key，请到 系统管理 → API 配置 中设置")

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
                "model": "deepseek-v4-pro",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096
            }
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        raise RuntimeError(f"DeepSeek API 错误: {resp.status_code} {resp.text[:200]}")


def _extract_json(text: str) -> dict:
    """从 AI 回复中提取 JSON"""
    text = text.strip()
    # 移除 markdown 代码块
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)
