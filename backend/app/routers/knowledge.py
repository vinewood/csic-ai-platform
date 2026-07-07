"""知识库与文档管理路由"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import KnowledgeBase, KnowledgeDoc
from ..schemas import MessageResponse
from ..config import UPLOAD_DIR
import os, uuid, shutil

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


# ── 知识库 CRUD ──────────────────────────────────────────────


@router.get("")
async def list_knowledge_bases(db: AsyncSession = Depends(get_db)):
    """获取所有知识库列表"""
    result = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.id))
    kbs = result.scalars().all()
    return [
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "type": kb.type,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
            "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
        }
        for kb in kbs
    ]


@router.post("", response_model=MessageResponse)
async def create_knowledge_base(
    name: str,
    description: str = "",
    type: str = "教学",
    db: AsyncSession = Depends(get_db),
):
    """创建新的知识库"""
    kb = KnowledgeBase(name=name, description=description, type=type)
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return MessageResponse(
        message="知识库创建成功",
        data={
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "type": kb.type,
        },
    )


@router.put("/{kb_id}", response_model=MessageResponse)
async def update_knowledge_base(
    kb_id: int,
    name: str = "",
    description: str = "",
    type: str = "",
    db: AsyncSession = Depends(get_db),
):
    """更新知识库信息"""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if name:
        kb.name = name
    if description:
        kb.description = description
    if type:
        kb.type = type
    await db.commit()
    await db.refresh(kb)
    return MessageResponse(
        message="知识库更新成功",
        data={
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "type": kb.type,
        },
    )


@router.delete("/{kb_id}", response_model=MessageResponse)
async def delete_knowledge_base(kb_id: int, db: AsyncSession = Depends(get_db)):
    """删除知识库（级联删除关联文档）"""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # 删除关联的物理文件
    docs_result = await db.execute(
        select(KnowledgeDoc).where(KnowledgeDoc.kb_id == kb_id)
    )
    for doc in docs_result.scalars().all():
        if doc.filepath and os.path.exists(doc.filepath):
            os.remove(doc.filepath)
    await db.delete(kb)
    await db.commit()
    return MessageResponse(message="知识库已删除")


# ── 文档管理 ────────────────────────────────────────────────


@router.get("/{kb_id}/docs")
async def list_documents(kb_id: int, db: AsyncSession = Depends(get_db)):
    """获取知识库中的文档列表"""
    # 先验证知识库存在
    kb_result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")
    result = await db.execute(
        select(KnowledgeDoc)
        .where(KnowledgeDoc.kb_id == kb_id)
        .order_by(KnowledgeDoc.id)
    )
    docs = result.scalars().all()
    return [
        {
            "id": doc.id,
            "kb_id": doc.kb_id,
            "title": doc.title,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
        for doc in docs
    ]


@router.post("/{kb_id}/docs", response_model=MessageResponse)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传文档到知识库"""
    kb_result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 保存文件到 UPLOAD_DIR
    ext = os.path.splitext(file.filename or "file")[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 存储元数据
    doc = KnowledgeDoc(
        kb_id=kb_id,
        title=file.filename or saved_name,
        filename=saved_name,
        filepath=file_path,
        content="",
        file_size=len(content),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return MessageResponse(
        message="文档上传成功",
        data={
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_size": doc.file_size,
        },
    )


@router.get("/{kb_id}/docs/{doc_id}")
async def get_document(
    kb_id: int,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取文档详情"""
    result = await db.execute(
        select(KnowledgeDoc).where(
            KnowledgeDoc.id == doc_id, KnowledgeDoc.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "id": doc.id,
        "kb_id": doc.kb_id,
        "title": doc.title,
        "filename": doc.filename,
        "filepath": doc.filepath,
        "content": doc.content,
        "file_size": doc.file_size,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.put("/{kb_id}/docs/{doc_id}", response_model=MessageResponse)
async def update_document(
    kb_id: int,
    doc_id: int,
    title: str = "",
    content: str = "",
    db: AsyncSession = Depends(get_db),
):
    """更新文档标题或内容"""
    result = await db.execute(
        select(KnowledgeDoc).where(
            KnowledgeDoc.id == doc_id, KnowledgeDoc.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if title:
        doc.title = title
    if content:
        doc.content = content
    await db.commit()
    await db.refresh(doc)
    return MessageResponse(
        message="文档更新成功",
        data={
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
        },
    )


@router.delete("/{kb_id}/docs/{doc_id}", response_model=MessageResponse)
async def delete_document(
    kb_id: int,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除文档（同时删除物理文件）"""
    result = await db.execute(
        select(KnowledgeDoc).where(
            KnowledgeDoc.id == doc_id, KnowledgeDoc.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 删除物理文件
    if doc.filepath and os.path.exists(doc.filepath):
        os.remove(doc.filepath)
    await db.delete(doc)
    await db.commit()
    return MessageResponse(message="文档已删除")
