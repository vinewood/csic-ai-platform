"""应用配置"""

import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"

# 创建目录
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 数据库
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/csic.db"

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "csic-***REMOVED-PASSWORD***-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 默认密码（首次安装使用）
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "***REMOVED-PASSWORD***")

# CORS
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Dify API（本地 Docker 部署，默认 localhost:5001）
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://localhost:5001")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")

# 服务端口
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ---- LLM API Key 内存缓存（从数据库 ApiConfig 表加载） ----
_api_keys: dict[str, str] = {}

def set_api_config(provider: str, key: str):
    _api_keys[provider] = key

def get_api_config(provider: str) -> str:
    return _api_keys.get(provider, os.getenv(f"{provider.upper()}_API_KEY", ""))

async def reload_api_keys():
    """从数据库 ApiConfig 表重新加载所有 API Key"""
    try:
        from app.database import async_session
        from app.models import ApiConfig
        from sqlalchemy import select
        async with async_session() as session:
            result = await session.execute(select(ApiConfig))
            for cfg in result.scalars().all():
                config_json = cfg.config_json or {}
                if "key" in config_json and config_json["key"]:
                    _api_keys[cfg.provider] = config_json["key"]
    except Exception:
        pass  # 数据库还未初始化
