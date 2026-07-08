from collections.abc import AsyncGenerator
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

"""
数据库引擎、会话工厂、Base 声明
"""
# ── 异步引擎 ──
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

# ── 异步会话工厂 ──
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 所有实体类的基类
class Base(DeclarativeBase):
    pass

# ── FastAPI 依赖：获取数据库会话 ──
async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    # 每个请求获取一个独立数据库会话，请求结束自动关闭
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()