"""认证模块：JWT 令牌处理 + 密码哈希（兼容 bcrypt 4.x/5.x）"""

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
import hashlib
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 — 兼容 passlib $2b$ 和原生 bcrypt 哈希"""
    try:
        # 尝试原生 bcrypt.checkpw
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        pass
    try:
        # 兼容 passlib 格式
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.verify(plain_password, hashed_password)
    except Exception:
        pass
    # 最简兜底：重新哈希比较
    salt = hashed_password[:29]  # $2b$12$ + 22 chars
    new_hash = bcrypt.hashpw(plain_password.encode("utf-8"), salt.encode("utf-8"))
    return new_hash.decode("utf-8") == hashed_password


def get_password_hash(password: str) -> str:
    """生成密码哈希 — 使用 bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# ---- JWT ----

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """从请求头中提取当前用户"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return decode_token(credentials.credentials)


async def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """仅允许 admin 角色访问"""
    payload = decode_token(credentials.credentials)
    role = payload.get("role", "user")
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    return payload
