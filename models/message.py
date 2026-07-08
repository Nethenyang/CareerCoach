from sqlalchemy import BigInteger, DateTime, Integer, String, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base
from datetime import datetime

"""
对话消息表
"""
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="消息主键")
    conversation_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True, comment="所属会话 ID")
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="消息角色：user / assistant")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="输入 token 数（仅 assistant 消息）")
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="输出 token 数（仅 assistant 消息）")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
