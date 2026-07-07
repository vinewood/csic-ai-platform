"""管理后台路由 — 仅 admin 角色可访问 + 集成项目 SSO 代理"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

# 兼容老版本 auth.py 没有 get_admin_user 的情况
try:
    from ..auth import get_admin_user
except ImportError:
    from ..auth import get_current_user
    async def get_admin_user(credentials=None):
        user = await get_current_user(credentials) if credentials else get_current_user()
        if isinstance(user, dict) and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="仅管理员可访问")
        return user

router = APIRouter(prefix="/api/admin", tags=["管理后台"])

# ---- SSO 代理配置 ----
SSO_PROXY = {
    "dify": {
        "name": "Dify AI 平台",
        "url": "http://127.0.0.1:5001",
        "icon": "Robot",
        "desc": "知识库管理 / AI 工作流 / 对话应用",
    },
    "rsshub": {
        "name": "RSSHub",
        "url": "http://127.0.0.1:1200",
        "icon": "Rss",
        "desc": "RSS 订阅源生成 / 新闻聚合",
    },
    "gpt_academic": {
        "name": "GPT Academic",
        "url": "http://127.0.0.1:8765",
        "icon": "School",
        "desc": "学术研究辅助 / 文献分析",
    },
}


@router.get("/integrations")
async def list_integrations(admin=Depends(get_admin_user)):
    """获取已集成的开源项目列表及状态"""
    results = []
    for key, cfg in SSO_PROXY.items():
        status = "unknown"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(cfg["url"])
                status = "online" if r.status_code < 500 else "error"
        except Exception:
            status = "offline"
        results.append({**cfg, "id": key, "status": status})
    return {"integrations": results}


@router.get("/proxy/{service}/{path:path}")
async def sso_proxy(service: str, path: str, request: Request, admin=Depends(get_admin_user)):
    """SSO 代理：将管理后台请求转发到集成项目"""
    target = SSO_PROXY.get(service)
    if not target:
        raise HTTPException(status_code=404, detail="未知服务")

    target_url = f"{target['url']}/{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(target_url)
            return Response(content=resp.content, status_code=resp.status_code)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"代理失败: {str(e)}")


# ---- 仅 admin 可访问的系统设置占位 ----
@router.get("/settings")
async def system_settings(admin=Depends(get_admin_user)):
    """系统设置 — 仅管理员可查看"""
    return {
        "message": "系统管理设置（仅 admin）",
        "available": ["API Keys", "用户管理", "日志查看", "系统监控"],
    }
