from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

"""
用户表
"""
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键，用户 ID")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="登录用户名，唯一")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="加密后的密码")
    nickname: Mapped[str] = mapped_column(String(50), default="", comment="昵称/显示名称")
    avatar_url: Mapped[str] = mapped_column(String(500), default="", comment="头像 OSS 地址")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态：1=正常, 0=禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="最后登录时间")
