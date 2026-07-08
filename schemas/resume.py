from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

"""
简历请求与响应模型

Attributes:
    type: 问题类型枚举
    location: 问题在简历中的定位
    issue: 问题描述
    before: 修改前内容
    after: 修改后建议内容
"""
# ── 单条建议（AI 结构化输出） ──
class ResumeSuggestion(BaseModel):
    type: Literal["verb_replacement", "missing_quantification", "structure", "jd_gap"] = Field(
        description="问题类型：verb_replacement=弱动词替换，missing_quantification=缺少量化指标，structure=结构/格式问题，jd_gap=与目标JD关键词差距"
    )
    location: str = Field(description="问题定位，如『工作经历 - 美团 - 第2项』")
    issue: str = Field(description="问题描述，一句话说明")
    before: str = Field(description="修改前的原文内容")
    after: str = Field(description="修改后的建议内容")

# ── 完整分析结果（AI 结构化输出） ──
class ResumeAnalysis(BaseModel):
    suggestions: List[ResumeSuggestion] = Field(description="优化建议列表，按重要性排序")


# ── 能力评估结果 ──
class AbilityProfile(BaseModel):
    tech_direction: Literal["后端", "前端", "算法", "数据", "全栈", "测试", "运维"]
    experience_level: Literal["初级", "中级", "高级", "专家"]
    skills: list[str] = Field(description="核心技能，5-10 项")
    strengths: list[str] = Field(description="优势，3-5 项")
    weaknesses: list[str] = Field(description="不足，2-4 项")
    summary: str = Field(description="综合评价，100-200 字")


# ── 梯队建议 ──
class TierSuggestion(BaseModel):
    tier: Literal["startup", "mid", "big_edge", "big_core"]
    reasoning: str = Field(description="推荐理由")
    alternative_tiers: list[str] = Field(description="备选梯队，1-2 个")


# ── 单项技能评分 ──
class SkillScore(BaseModel):
    skill: str = Field(description="技能维度名称，如「前端框架」「系统设计」")
    score: int = Field(description="该维度评分，0-100 整数")


# ── 评分报告 ──
class ScoreAssessment(BaseModel):
    overall_score: int = Field(description="综合评分，0-100 整数")
    skill_scores: list[SkillScore] = Field(description="各技能维度评分列表，5-8 项")


# ── 维度子项（优点/不足/建议） ──
class DimensionSubItem(BaseModel):
    name: str = Field(description="子项名称，如「语言清晰度」「逻辑结构」")
    pros: str = Field(description="优点分析，2-3句，引用简历具体内容")
    cons: str = Field(description="不足分析，2-3句，引用简历具体内容")
    suggestion: str = Field(description="改进建议，2-3句，给出可操作的建议")


# ── 维度评分（含子项） ──
class DimensionScore(BaseModel):
    name: str = Field(description="维度名称：语言与表达|信息完整性|内容相关性|简历专业性")
    score: int = Field(description="该维度评分，0-100 整数")
    sub_items: list[DimensionSubItem] = Field(description="子项列表，4-5项")


# ── 战略建议（分类） ──
class StrategicSuggestion(BaseModel):
    title: str = Field(description="建议类别标题，如「立即优化简历结构与信息完整性」")
    items: list[str] = Field(description="具体建议，2-3条")


# ── 维度分析报告 ──
class DimensionReport(BaseModel):
    strategic_suggestions: list[StrategicSuggestion] = Field(description="综合建议，3个类别")
    dimensions: list[DimensionScore] = Field(description="4个维度的详细分析")


# ── 分析请求体（target_jd 可选，可能较长，走 body） ──
class AnalyzeRequest(BaseModel):
    target_jd: str = ""

# ── 上传响应 ──
class ResumeUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_url: str
    created_at: datetime

# ── 简历列表项 ──
class ResumeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    total_issues: int
    created_at: datetime

# ── 简历详情响应 ──
class ResumeDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    filename: str
    file_url: str
    raw_text: Optional[str] = None
    target_jd: Optional[str] = None
    suggestions: Optional[list] = None
    total_issues: int
    created_at: datetime

# ── 分析结果响应 ──
class ResumeAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    suggestions: List[ResumeSuggestion]
    total_issues: int
    ability_profile: Optional[AbilityProfile] = None
    tier_suggestion: Optional[TierSuggestion] = None
    retrieved_jds: Optional[list[dict]] = None
    score_assessment: Optional[ScoreAssessment] = None
    dimension_report: Optional[DimensionReport] = None
    conversation_id: Optional[int] = Field(default=None, description="该简历已关联的对话 ID，无则 None（由路由层注入，Resume ORM 本身无此属性）")
