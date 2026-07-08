from typing import Any, Optional
from pydantic import BaseModel

"""
统一后端返回响应模型

Attributes:
    code: 业务状态码，200 表示成功
    message: 提示信息
    data: 返回数据，可为任意类型
"""
class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "ApiResponse":
        """成功响应快捷方法"""
        return cls(code=200, message=message, data=data)
