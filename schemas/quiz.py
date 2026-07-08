from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


# ═══════════════════════════════════════════════════════════
# 请求模型
# ═══════════════════════════════════════════════════════════

class CreateQuizRequest(BaseModel):
    conversation_id: int
    title: str
    question_count: int = 8
    user_requirements: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("测验标题须在 1-100 字符之间")
        return v

    @field_validator("question_count")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v not in (5, 8, 10, 15):
            raise ValueError("题目数量只能为 5 / 8 / 10 / 15")
        return v


class AnswerQuestionRequest(BaseModel):
    question_id: int
    selected_option_id: str


# ═══════════════════════════════════════════════════════════
# 响应模型
# ═══════════════════════════════════════════════════════════

class QuizOptionResponse(BaseModel):
    id: str
    label: str
    text: str
    description: str


class QuizQuestionResponse(BaseModel):
    id: int
    session_id: int
    stem: str
    options: list[QuizOptionResponse]
    correct_option_id: str
    explanation: str
    topic_tags: Optional[list[str]] = None
    category: Optional[str] = None
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class QuizSessionResponse(BaseModel):
    id: int
    user_id: int
    conversation_id: int
    title: str
    target_jd: Optional[str] = None
    question_count: int
    user_requirements: Optional[str] = None
    status: str
    score: Optional[int] = None
    report: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizListItem(BaseModel):
    id: int
    title: str
    question_count: int
    status: str
    score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnswerQuestionResponse(BaseModel):
    is_correct: bool
    correct_option_id: str
    explanation: str


class CreateQuizResponse(BaseModel):
    session: QuizSessionResponse
    questions: list[QuizQuestionResponse]


class QuizDetailResponse(BaseModel):
    session: QuizSessionResponse
    questions: list[QuizQuestionResponse]


# ═══════════════════════════════════════════════════════════
# AI 输出模型（extract_json 后校验）
# ═══════════════════════════════════════════════════════════

class AIQuizOption(BaseModel):
    id: str          # "a", "b", "c", "d"
    label: str       # "A", "B", "C", "D"
    text: str
    description: str


class AIQuizQuestion(BaseModel):
    stem: str
    options: list[AIQuizOption]
    correct_option_id: str
    explanation: str
    topic_tags: list[str]
    category: str    # basic / project / behavioral


class AIQuizGenerateOutput(BaseModel):
    questions: list[AIQuizQuestion]


class CategoryScore(BaseModel):
    name: str
    correct: int
    total: int
    percent: int


class SuggestionItem(BaseModel):
    topic: str
    tip: str


class AIQuizReportOutput(BaseModel):
    total_questions: int
    correct_count: int
    incorrect_count: int
    score_percent: int
    grade: str
    categories: list[CategoryScore]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[SuggestionItem]

    @field_validator("score_percent", "correct_count", "incorrect_count", mode="before")
    @classmethod
    def coerce_int(cls, v: object) -> int:
        return int(float(str(v)))
