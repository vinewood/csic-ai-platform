"""
gpt_academic 集成服务
提取核心学术功能，包装为 FastAPI 可调用的函数
"""

import sys
import os

# 添加 gpt_academic 路径
GPT_ACADEMIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "gpt_academic")
if os.path.exists(GPT_ACADEMIC_DIR):
    sys.path.insert(0, GPT_ACADEMIC_DIR)


async def academic_chat(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """调用 gpt_academic 核心函数进行学术对话"""
    try:
        from crazy_functional import get_crazy_functionals
        from toolbox import ChatBotWithCookies

        # 初始化 gpt_academic 聊天机器人
        chatbot = ChatBotWithCookies()
        # 调用核心功能
        result = chatbot.get_response(prompt)
        return result
    except ImportError as e:
        return f"[gpt_academic 未加载: {e}]"
    except Exception as e:
        return f"[gpt_academic 错误: {e}]"


async def search_papers(query: str, max_results: int = 10) -> list:
    """使用 gpt_academic 的论文搜索功能"""
    try:
        from crazy_functional import 联网搜索论文
        results = await 联网搜索论文(query, max_results)
        return results
    except Exception as e:
        return [{"title": f"搜索暂不可用: {e}", "url": "", "abstract": ""}]


async def generate_outline(topic: str) -> str:
    """使用 gpt_academic 生成论文大纲"""
    prompt = f"请为以下课题生成规范的论文大纲：\n{topic}\n\n要求包含：\n1. 选题背景与意义\n2. 国内外研究现状\n3. 研究目标与内容\n4. 研究方法\n5. 预期创新点\n6. 进度安排"
    return await academic_chat(prompt)
