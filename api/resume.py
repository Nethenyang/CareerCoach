import logging
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from middleware.auth import get_current_user_id
from schemas.response import ApiResponse
from schemas.resume import AnalyzeRequest, ResumeAnalysisResponse, ResumeUploadResponse
from services.resume import get_resume_by_id, upload_resume, validate_file, analyze_resume_record
from services.conversation import get_conversation_by_resume_id

"""
简历接口：上传、分析、查询、删除
"""
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["简历"])

# ── 上传简历 ──
@router.post("/upload", response_model=ApiResponse)
async def upload(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # 读取文件内容
    file_bytes = await file.read()
    # 校验类型与大小
    err = validate_file(file.filename or "", len(file_bytes))
    if err:
        return ApiResponse(code=400, message=err)

    resume = await upload_resume(db, user_id, file.filename or "unknown.pdf", file_bytes)
    return ApiResponse.success(
        data=ResumeUploadResponse.model_validate(resume).model_dump(),
        message="上传成功",
    )

# ── 查询简历分析结果 ──
@router.get("/{resume_id}", response_model=ApiResponse)
async def get_detail(
    resume_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    resume = await get_resume_by_id(db, resume_id)
    if not resume:
        return ApiResponse(code=404, message="简历不存在")
    if resume.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该简历")
    if not resume.suggestions:
        return ApiResponse(code=422, message="该简历尚未分析")

    data = ResumeAnalysisResponse.model_validate(resume).model_dump()
    # 注入该简历已关联的对话 ID（前端据此判断是否已创建对话，避免重复创建）
    conv = await get_conversation_by_resume_id(db, user_id, resume_id)
    data["conversation_id"] = conv.id if conv else None
    return ApiResponse.success(data=data)

# ── 分析简历 ──
@router.post("/analyze/{resume_id}", response_model=ApiResponse)
async def analyze(
    resume_id: int,
    req: AnalyzeRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # 校验简历归属
    resume = await get_resume_by_id(db, resume_id)
    if not resume:
        return ApiResponse(code=404, message="简历记录不存在")
    if resume.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该简历")
    if not resume.raw_text:
        return ApiResponse(code=422, message="简历文本解析失败，无法分析")

    # 执行分析
    try:
        analyzed = await analyze_resume_record(db, resume, req.target_jd)
    except Exception:
        logger.exception("简历分析失败 resume_id=%s user_id=%s", resume_id, user_id)
        return ApiResponse(code=500, message="AI 服务异常，请稍后重试")

    return ApiResponse.success(
        data=ResumeAnalysisResponse.model_validate(analyzed).model_dump(),
        message="分析完成",
    )
