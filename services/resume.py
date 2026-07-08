import io
import os
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.resume import Resume
from ai.workflow.pipeline import get_pipeline
from util.oss_client import upload_file, delete_file, extract_key

"""
简历业务逻辑：上传、分析、查询、删除
"""
# ── 允许的文件扩展名与大小 ──
ALLOWED_EXT = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ── 校验文件类型与大小 ──
def validate_file(filename: str, file_size: int) -> Optional[str]:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return "仅支持 PDF 格式"
    if file_size > MAX_FILE_SIZE:
        return "文件大小超过 10MB"
    return None

# 直接接受 bytes，避免依赖本地文件路径（适配 OSS 存储场景）
def parse_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(parts).strip()

# ── 上传简历 ──
async def upload_resume(db: AsyncSession, user_id: int, filename: str, file_bytes: bytes) -> Resume:

    ext = os.path.splitext(filename)[1].lower()
    key = f"resumes/{user_id}/{uuid.uuid4().hex}{ext}"
    file_url = upload_file(key, file_bytes, content_type="application/pdf")

    # 解析文本（失败不阻断流程，raw_text 留空）—— 直接用内存中的 bytes，无需本地文件
    raw_text = parse_pdf_text(file_bytes)
    # 入库
    resume = Resume(
        user_id=user_id,
        filename=filename,
        file_url=file_url,
        raw_text=raw_text or None,
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume

# ── 根据 ID 查询简历 ──
async def get_resume_by_id(db: AsyncSession, resume_id: int) -> Optional[Resume]:
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    return result.scalar_one_or_none()

# ── 分析简历（6阶段管道：分析→评估→评分→维度→梯队→JD检索） ──
async def analyze_resume_record(db: AsyncSession, resume: Resume, target_jd: str = "") -> Resume:
    # 1. 获取编译好的管道
    pipeline = get_pipeline()
    # 2. 构造输入状态
    input_state = {
        "resume_text": resume.raw_text,
        "target_jd": target_jd,
    }
    # 3. 异步执行六步管道
    result = await pipeline.ainvoke(input_state)
    # 4. 把 6 个产物写回 resume 对象
    resume.suggestions = result["suggestions"]
    resume.total_issues = len(result["suggestions"])
    resume.ability_profile = result["ability_profile"]
    resume.score_assessment = result.get("score_assessment")
    resume.dimension_report = result.get("dimension_report")
    resume.tier_suggestion = result["tier_suggestion"]
    resume.retrieved_jds = result["retrieved_jds"]
    # 5. 如果传了 target_jd 也存下来
    if target_jd:
        resume.target_jd = target_jd
    # 6. 刷新数据库
    await db.flush()
    await db.refresh(resume)
    return resume

# ── 查询用户简历列表（按创建时间倒序） ──
async def list_resumes(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10) -> tuple[list[Resume], int]:
    from sqlalchemy import func
    count_query = select(func.count()).select_from(Resume).where(Resume.user_id == user_id)
    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = (
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    return result.scalars().all(), total

# ── 删除简历（同时删 OSS 文件） ──
async def delete_resume(db: AsyncSession, resume_id: int) -> bool:
    resume = await get_resume_by_id(db, resume_id)
    if not resume:
        return False
    # 删 OSS 文件
    if resume.file_url:
        try:
            delete_file(extract_key(resume.file_url))
        except Exception:
            # OSS 删除失败不阻断数据库删除，仅记录；此处可接 logger
            pass
    await db.delete(resume)
    await db.flush()
    return True
