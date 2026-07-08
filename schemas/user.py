from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

"""
用户相关请求/响应模型

Attributes:
    username: 登录用户名，3-50 字符
    password: 密码，6-128 字符
    nickname: 昵称/显示名称
"""
# ── 注册请求 ──
class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("用户名长度须在 3-50 字符之间")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 128:
            raise ValueError("密码长度须在 6-128 字符之间")
        return v

# ── 登录请求 ──
class LoginRequest(BaseModel):
    username: str
    password: str

# ── 用户信息响应 ──
class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str
    avatar_url: str
    status: int
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True
