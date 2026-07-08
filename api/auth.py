from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from schemas.response import ApiResponse
from schemas.user import LoginRequest, RegisterRequest, UserResponse
from services.user import get_user_by_username, login_user, register_user

"""
认证接口：注册、登录
"""
router = APIRouter(prefix="/api/auth", tags=["认证"])

# ── 用户注册 ──
@router.post("/register", response_model=ApiResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    existing = await get_user_by_username(db, req.username)
    if existing:
        return ApiResponse(code=409, message="用户名已存在")

    user = await register_user(db, req.username, req.password, req.nickname or "")
    return ApiResponse.success(
        data=UserResponse.model_validate(user).model_dump(),
        message="注册成功",
    )

# ── 用户登录 ──
@router.post("/login", response_model=ApiResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await login_user(db, req.username, req.password)
    if not user:
        return ApiResponse(code=401, message="用户名或密码错误")

    return ApiResponse.success(
        data=UserResponse.model_validate(user).model_dump(),
        message="登录成功",
    )
