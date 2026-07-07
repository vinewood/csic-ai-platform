"""FastAPI 应用主入口"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保 backend 在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import CORS_ORIGINS, HOST, PORT, reload_api_keys
from app.database import init_db, seed_db
from app.routers import (
    auth_router, chat, users, rss, email, files, academic, api_config,
    knowledge, skills, research, teaching, video, dify_kb, admin,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库 + 加载 API Key"""
    await init_db()
    await seed_db()
    await reload_api_keys()
    yield


app = FastAPI(
    title="中船党校 AI 平台 API",
    description="CSIC Party School AI Platform Backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件（前端构建产物）
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "www")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(STATIC_DIR, "static")), name="static")
    app.mount("/img", StaticFiles(directory=os.path.join(STATIC_DIR, "img")), name="img")
    app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")

# 注册路由
app.include_router(auth_router.router)
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(rss.router)
app.include_router(email.router)
app.include_router(files.router)
app.include_router(academic.router)
app.include_router(api_config.router)
app.include_router(knowledge.router)
app.include_router(skills.router)
app.include_router(research.router)
app.include_router(teaching.router)
app.include_router(video.router)
app.include_router(dify_kb.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
async def root():
    """重定向到前端"""
    from fastapi.responses import FileResponse
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CSIC AI Platform API is running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
