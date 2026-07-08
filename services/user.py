from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import hash_password, verify_password
from models.user import User

"""
用户业务逻辑：注册、登录、查询
"""
# ── 根据用户名查询用户 ──
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

# ── 用户注册 ──
async def register_user(db: AsyncSession, username: str, password: str, nickname: str = "") -> User:
    hashed_pw = hash_password(password)
    user = User(
        username=username,
        password=hashed_pw,
        nickname=nickname or username,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

# ── 用户登录 ──
async def login_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    # 更新最后登录时间
    user.last_login_at = datetime.now()
    await db.flush()
    return user
