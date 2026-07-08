from fastapi import Header, HTTPException

"""
X-User-Id 鉴权依赖：从请求头提取用户身份并校验
"""
# ── 获取当前用户 ID ──
async def get_current_user_id(x_user_id: str | None = Header(None, alias="X-User-Id")) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="未登录或用户信息无效")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="未登录或用户信息无效")
