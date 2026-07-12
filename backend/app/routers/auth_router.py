"""认证路由：登录/注册/个人设置"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, TokenResponse, UserCreate, UserUpdateProfile, MessageResponse
from ..auth import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="账号正在等待管理员审核，请稍后重试")
    if user.status == "rejected":
        raise HTTPException(status_code=403, detail="账号审核未通过，请联系管理员")

    if not user.is_active:
        user.is_active = True
        await db.commit()

    token = create_access_token({
        "sub": user.username, "id": user.id,
        "name": user.username, "role": user.role
    })
    return TokenResponse(
        access_token=token, username=user.username,
        role=user.role, email=user.email or "", real_name=user.real_name or ""
    )


@router.post("/register", response_model=MessageResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册 — 提交后等待管理员审核"""
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    if req.email:
        result2 = await db.execute(select(User).where(User.email == req.email))
        if result2.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=req.username,
        email=req.email or "",
        real_name=req.real_name or "",
        hashed_password=get_password_hash(req.password),
        is_active=False,
        status="pending",
        role="user",
    )
    db.add(user)
    await db.commit()
    return MessageResponse(message="注册成功！请等待管理员审核后登录")


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.put("/me/profile")
async def update_profile(
    req: UserUpdateProfile,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新个人设置（邮箱/密码/姓名）"""
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    updated = []
    if req.email and req.email != user.email:
        # 检查邮箱唯一性
        exist = await db.execute(select(User).where(User.email == req.email, User.id != user.id))
        if exist.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        user.email = req.email
        updated.append("邮箱")

    if req.password:
        user.hashed_password = get_password_hash(req.password)
        updated.append("密码")

    if req.real_name is not None:
        user.real_name = req.real_name
        updated.append("姓名")

    await db.commit()
    return {"message": f"已更新: {', '.join(updated)}" if updated else "无变更"}
