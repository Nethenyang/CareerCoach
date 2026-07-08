from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

"""
简历表
"""
class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键，简历 ID")
    user_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True, comment="所属用户 ID")
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件访问地址")
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="解析后的简历纯文本")
    target_jd: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="目标岗位 JD 文本（可选）")
    suggestions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="结构化优化建议列表")
    ability_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="能力评估结果")
    tier_suggestion: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="梯队建议")
    retrieved_jds: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="检索到的 JD 列表")
    score_assessment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="评分报告（综合评分+技能维度评分）")
    dimension_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="维度分析报告（4维度+战略建议）")
    total_issues: Mapped[int] = mapped_column(Integer, default=0, comment="问题总数（冗余字段，加速列表查询）")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
