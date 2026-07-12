"""用户管理路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User
from ..schemas import UserOut, UserCreate, MessageResponse
from ..auth import get_password_hash, get_current_user

# Admin-only guard
try:
    from ..auth import get_admin_user
except ImportError:
    async def get_admin_user(credentials=None):
        raise HTTPException(status_code=403, detail="无权限")

router = APIRouter(prefix="/api/users", tags=["用户管理"])


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id, "username": user.username, "email": user.email or "",
        "real_name": user.real_name or "", "is_active": user.is_active,
        "status": user.status or "pending", "role": user.role,
        "created_at": str(user.created_at)[:19] if user.created_at else ""
    }


@router.get("")
async def list_users(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(User).order_by(User.id.desc()))
    return [_user_to_dict(u) for u in result.scalars().all()]


@router.post("", response_model=MessageResponse)
async def create_user(req: UserCreate, db: AsyncSession = Depends(get_db), admin=Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户已存在")
    user = User(
        username=req.username, email=req.email,
        real_name=req.real_name or "",
        hashed_password=get_password_hash(req.password or "***REMOVED-PASSWORD***"),
        is_active=True, status="active", role="user",
    )
    db.add(user)
    await db.commit()
    return MessageResponse(message="用户已创建")


@router.put("/{user_id}", response_model=MessageResponse)
async def update_user(user_id: int, req: dict, db: AsyncSession = Depends(get_db), admin=Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.get("name") is not None:
        user.username = req["name"]
    if req.get("email") is not None:
        user.email = req["email"]
    await db.commit()
    return MessageResponse(message="用户已更新")


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user)
    await db.commit()
    return MessageResponse(message="用户已删除")


@router.post("/{user_id}/approve", response_model=MessageResponse)
async def approve_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = "active"
    user.is_active = True
    await db.commit()
    return MessageResponse(message=f"用户 {user.username} 已审批通过")


@router.post("/{user_id}/reject", response_model=MessageResponse)
async def reject_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = "rejected"
    user.is_active = False
    await db.commit()
    return MessageResponse(message=f"用户 {user.username} 已拒绝")
