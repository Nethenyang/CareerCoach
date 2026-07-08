from pydantic import BaseModel

"""
对话相关请求模型
"""
# ── 对话请求 ──
class ChatRequest(BaseModel):
    message: str
