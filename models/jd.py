from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

"""
JD 知识库元数据表
"""
class JdKnowledge(Base):
    __tablename__ = "jd_knowledge"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="主键，JD ID")
    company: Mapped[str] = mapped_column(String(100), nullable=False, comment="公司名称")
    position: Mapped[str] = mapped_column(String(100), nullable=False, comment="岗位名称")
    tier: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="梯队：startup/mid/big_edge/big_core")
    tech_direction: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="技术方向：后端/前端/算法/数据/全栈/测试/运维")
    requirements: Mapped[str] = mapped_column(Text, nullable=False, comment="岗位要求正文（用于向量化与检索）")
    source_url: Mapped[str] = mapped_column(String(500), default="", comment="JD 来源链接")
    vector_indexed: Mapped[int] = mapped_column(Integer, default=0, comment="是否已向量化：1=是 0=否")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
