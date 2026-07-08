from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

"""
对话会话表
"""
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键，对话 ID")
    user_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), nullable=False, comment="所属用户 ID")
    resume_id: Mapped[int | None] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), nullable=True, index=True, comment="关联简历 ID")
    title: Mapped[str] = mapped_column(String(100), default="新对话", comment="对话标题")
    message_count: Mapped[int] = mapped_column(Integer, default=0, comment="消息总数")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="最近一条消息时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
