"""认证路由：登录"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, TokenResponse, UserCreate, MessageResponse
from ..auth import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": user.username, "id": user.id, "name": user.username, "role": user.role})
    return TokenResponse(access_token=token, username=user.username)


@router.post("/register", response_model=MessageResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户已存在")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password or "***REMOVED-PASSWORD***"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return MessageResponse(message="用户创建成功")


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
