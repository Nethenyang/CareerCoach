from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

"""
JD 知识库请求与响应模型
"""
# ── 梯队枚举 ──
Tier = Literal["startup", "mid", "big_edge", "big_core"]

# ── 技术方向枚举 ──
TechDirection = Literal["后端", "前端", "算法", "数据", "全栈", "测试", "运维"]

# ── 录入请求 ──
class JdCreateRequest(BaseModel):
    company: str = Field(max_length=100, description="公司名称")
    position: str = Field(max_length=100, description="岗位名称")
    tier: Tier = Field(description="梯队：startup/mid/big_edge/big_core")
    tech_direction: TechDirection = Field(description="技术方向")
    requirements: str = Field(min_length=1, description="岗位要求正文（用于向量化与检索）")
    source_url: str = Field(default="", max_length=500, description="JD 来源链接")

# ── 批量导入请求 ──
class JdImportRequest(BaseModel):
    items: List[JdCreateRequest] = Field(description="JD 列表")

# ── 单条响应 ──
class JdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    tier: str
    tech_direction: str
    requirements: str
    source_url: str
    vector_indexed: int
    created_at: datetime

# ── 列表项（不含 requirements 全文，省流量） ──
class JdListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    tier: str
    tech_direction: str
    vector_indexed: int
    created_at: datetime
