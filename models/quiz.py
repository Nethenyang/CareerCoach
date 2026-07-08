from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

"""
测验会话表 + 测验题目表
"""


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键，测验会话 ID"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True, comment="所属用户 ID"
    )
    conversation_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True, comment="关联的对话 ID"
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="测验标题（用户输入）")
    target_jd: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JD 上下文快照")
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=8, comment="题目数量")
    user_requirements: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户自定义要求")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress", comment="in_progress / completed")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="总分（答对数）")
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="评估报告")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键，题目 ID"
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True, comment="所属测验会话 ID"
    )
    stem: Mapped[str] = mapped_column(Text, nullable=False, comment="题目题干")
    options: Mapped[list] = mapped_column(JSON, nullable=False, comment="选项列表 [{id, label, text, description}]")
    correct_option_id: Mapped[str] = mapped_column(String(10), nullable=False, comment="正确答案选项 ID")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, comment="正确答案的详细解释")
    topic_tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="主题标签")
    category: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="basic / project / behavioral")
    user_answer: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="用户选择的选项 ID")
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="用户是否答对")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="题目序号")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
