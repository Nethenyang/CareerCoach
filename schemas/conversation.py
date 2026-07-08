from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

"""
对话/消息请求与响应模型
"""
# ── 新建对话请求（必须绑定简历） ──
class CreateConversationRequest(BaseModel):
    resume_id: int
    title: Optional[str] = None

# ── 发送消息请求（content 为大参数，走 body） ──
class SendMessageRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("消息内容不能为空")
        return v

# ── 重命名请求（修改资源属性，走 body） ──
class RenameRequest(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("标题须在 1-100 字符之间")
        return v

# ── 对话信息响应 ──
class ConversationResponse(BaseModel):
    id: int
    user_id: int
    resume_id: Optional[int] = None
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ── 对话列表项 ──
class ConversationListItem(BaseModel):
    id: int
    title: str
    resume_id: Optional[int] = None
    resume_filename: Optional[str] = None
    message_count: int
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ── 消息响应 ──
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# ── 发送消息响应（含用户消息 + AI 回复） ──
class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    ai_message: MessageResponse

# ── 消息列表响应 ──
class MessageListResponse(BaseModel):
    conversation_id: int
    title: str
    messages: list[MessageResponse]
