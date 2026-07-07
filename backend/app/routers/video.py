"""视频管理路由"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import uuid
import json
import asyncio

from ..database import get_db
from ..models import User, VideoTask
from ..schemas import MessageResponse
from ..auth import get_current_user
from ..config import UPLOAD_DIR
from ..services.integrations import ASRService, DifyService

router = APIRouter(prefix="/api/video", tags=["视频"])

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}


# ---- Helper ----

async def _get_current_user_id(token_payload: dict, db: AsyncSession) -> int:
    username = token_payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user.id


# ---- 视频上传与处理 ----

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)

    # Validate file extension
    ext = os.path.splitext(file.filename or "video.mp4")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}，支持：{', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save file
    file_id = str(uuid.uuid4())
    save_filename = f"{file_id}{ext}"
    save_path = UPLOAD_DIR / save_filename

    content = await file.read()
    file_size = len(content)
    with open(save_path, "wb") as f:
        f.write(content)

    # Create video task with "processing" status
    task = VideoTask(
        title=file.filename or "未命名视频",
        filename=save_filename,
        filepath=str(save_path),
        status="processing",
        file_size=file_size,
        duration=0,
        user_id=user_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 后台处理视频
    asyncio.create_task(_process_video(task.id, str(save_path)))

    return {
        "id": task.id,
        "title": task.title,
        "filename": task.filename,
        "file_size": task.file_size,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


async def _process_video(task_id: int, filepath: str):
    """真实视频处理：ASR 转写 → Dify AI 摘要 + 闪卡"""
    from ..database import async_session as _async_session

    async with _async_session() as session:
        result = await session.execute(select(VideoTask).where(VideoTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return

        # Step 1: ASR 语音转文字
        asr_result = await ASRService.transcribe_file(filepath)
        transcript = asr_result.get("text", "转写失败: " + asr_result.get("message", "未知错误"))

        # Step 2: Dify AI 生成摘要
        summary = "AI 摘要生成中..."
        try:
            dify_summary = await DifyService.chat_blocking(
                query=f"请用200字中文概括以下视频转写内容：\n\n{transcript[:3000]}",
                user="admin"
            )
            summary = dify_summary.get("answer", summary)
        except Exception:
            pass

        # Step 3: Dify AI 生成知识闪卡
        flashcards = []
        try:
            dify_cards = await DifyService.chat_blocking(
                query=f"根据以下内容生成5道Q&A问答对（JSON数组格式{{\"question\":\"...\",\"answer\":\"...\"}}）：\n\n{transcript[:3000]}",
                user="admin"
            )
            answer = dify_cards.get("answer", "[]")
            import re
            match = re.search(r"\[.*\]", answer, re.DOTALL)
            if match:
                flashcards = json.loads(match.group())
        except Exception:
            flashcards = [{"question": "AI生成失败", "answer": "请重试"}]

        task.status = "done"
        task.transcript = transcript
        task.summary = summary
        task.flashcards = json.dumps(flashcards, ensure_ascii=False)

        # 保存视频到 Dify 知识库（可选）
        try:
            await DifyService.upload_file(filepath, "admin")
        except Exception:
            pass

        await session.commit()


@router.get("")
async def list_video_tasks(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    result = await db.execute(
        select(VideoTask)
        .where(VideoTask.user_id == user_id)
        .order_by(VideoTask.id.desc())
    )
    tasks = result.scalars().all()
    return {"videos": [
        {
            "id": t.id, "title": t.title, "filename": t.filename,
            "file_size": t.file_size, "duration": t.duration,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in tasks
    ]}


@router.get("/{video_id}")
async def get_video_task(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == video_id, VideoTask.user_id == user_id
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="视频任务不存在")

    return {
        "id": task.id,
        "title": task.title,
        "filename": task.filename,
        "filepath": task.filepath,
        "file_size": task.file_size,
        "duration": task.duration,
        "status": task.status,
        "transcript": task.transcript,
        "summary": task.summary,
        "flashcards": json.loads(task.flashcards) if task.flashcards else [],
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


@router.delete("/{video_id}")
async def delete_video_task(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == video_id, VideoTask.user_id == user_id
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="视频任务不存在")

    # Delete file from disk
    file_path = task.filepath
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass  # File may be locked or already deleted

    await db.delete(task)
    await db.commit()
    return MessageResponse(message="删除成功")
