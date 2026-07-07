"""CSIC Party School AI Platform - Main Application."""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from app.routers import page_router


# ── Static files cache middleware ──
class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add Cache-Control headers to static file responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith('/static/'):
            if '/lib/' in path or '/pages/' in path:
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            else:
                response.headers['Cache-Control'] = 'public, max-age=86400'
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache headers for static files (1 year for libs, 1 day for others)
app.add_middleware(CacheControlMiddleware)

# CORS (allow local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware: mock user for demo
@app.middleware("http")
async def mock_auth_middleware(request: Request, call_next):
    """In production, replace with real JWT auth. For now, inject a demo user."""
    class DemoUser:
        id = 1
        username = "demo"
        display_name = "张讲师"
        role = "teacher"
        default_workspace = "teaching"
    request.state.user = DemoUser()
    response = await call_next(request)
    return response


# Routers
app.include_router(page_router.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
