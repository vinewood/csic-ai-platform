"""用户管理路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User
from ..schemas import UserOut, UserCreate, MessageResponse
from ..auth import get_password_hash, get_current_user

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.post("", response_model=MessageResponse)
async def create_user(req: UserCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户已存在")
    user = User(
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password or "***REMOVED-PASSWORD***"),
    )
    db.add(user)
    await db.commit()
    return MessageResponse(message="用户已创建")


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user)
    await db.commit()
    return MessageResponse(message="用户已删除")
