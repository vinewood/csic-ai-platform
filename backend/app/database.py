"""数据库连接与会话管理"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    from . import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_db():
    """填充初始数据"""
    from .database import async_session
    from .models import User
    from .auth import get_password_hash

    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            return  # 已有用户

        admin = User(
            username="admin",
            email="admin@csic.cn",
            hashed_password=get_password_hash("dh24681357"),
            is_active=True,
        )
        session.add(admin)

        # 种子技能
        from .routers.skills import seed_skills
        await seed_skills(session)

        await session.commit()
