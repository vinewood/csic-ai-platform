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

    # Simulate 3-second processing
    task_id = task.id
    asyncio.create_task(_simulate_processing(task_id, db))

    return {
        "id": task.id,
        "title": task.title,
        "filename": task.filename,
        "file_size": task.file_size,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


async def _simulate_processing(task_id: int, db: AsyncSession):
    """Simulate video processing: wait 3 seconds, then update with mock results."""
    await asyncio.sleep(3)

    # Get a fresh session for the background task
    from ..database import async_session as _async_session

    async with _async_session() as session:
        result = await session.execute(select(VideoTask).where(VideoTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return

        task.status = "done"
        task.transcript = (
            "【视频转写结果】\n\n"
            "00:00 - 00:30 开场介绍\n"
            "大家好，欢迎收看本期视频。今天我们将探讨人工智能在教育领域的应用与发展。\n\n"
            "00:30 - 02:00 人工智能基础\n"
            "人工智能（AI）是计算机科学的一个重要分支，它致力于创建能够模拟人类智能的系统。\n"
            "近年来，深度学习技术的突破使得AI在图像识别、自然语言处理等领域取得了显著进展。\n\n"
            "02:00 - 04:00 AI教育应用\n"
            "在教育领域，AI技术正在改变传统的教学方式。\n"
            "智能辅导系统能够根据学生的学习情况提供个性化的学习建议。\n"
            "自适应学习平台可以动态调整教学内容和难度。\n\n"
            "04:00 - 05:30 案例分析\n"
            "以某高校为例，他们引入了AI辅助教学系统后，学生的学习效率提升了30%。\n"
            "教师的工作负担也得到了一定程度的缓解。\n\n"
            "05:30 - 06:00 总结\n"
            "人工智能正在深刻改变教育的面貌，未来还有更多的可能性等待我们去探索。"
        )
        task.summary = (
            "【视频摘要】\n\n"
            "本视频主要介绍了人工智能在教育领域的应用现状与发展趋势。\n"
            "首先阐述了人工智能的基本概念和核心技术，包括深度学习、自然语言处理等。\n"
            "随后重点分析了AI在教育中的典型应用场景，如智能辅导、自适应学习、自动评估等。\n"
            "通过实际案例展示了AI技术提升教学效果的潜力。\n"
            "最后展望了AI+教育的未来发展方向。"
        )
        task.flashcards = json.dumps(
            [
                {
                    "question": "人工智能(AI)的主要研究目标是什么？",
                    "answer": "创建能够模拟人类智能的系统，使计算机能够执行需要人类智能的任务。",
                },
                {
                    "question": "深度学习在AI教育中有哪些应用？",
                    "answer": "图像识别、自然语言处理、智能辅导系统、自适应学习平台等。",
                },
                {
                    "question": "AI辅助教学系统带来了哪些提升？",
                    "answer": "根据实际案例，学生的学习效率提升了30%，教师工作负担得到缓解。",
                },
                {
                    "question": "自适应学习平台的核心特点是什么？",
                    "answer": "能够根据学生的学习情况动态调整教学内容和难度，提供个性化的学习体验。",
                },
                {
                    "question": "AI在教育领域的未来发展方向是什么？",
                    "answer": "更智能的个性化学习、更精准的学习评估、更丰富的交互方式等。",
                },
            ],
            ensure_ascii=False,
        )
        task.duration = 360  # 6 minutes in seconds

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
