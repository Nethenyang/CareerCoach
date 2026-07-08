import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from schemas.response import ApiResponse
from schemas.jd import JdCreateRequest, JdImportRequest, JdResponse, JdListItem
from services.knowledge import create_jd, import_jds, list_jds, get_jd, delete_jd

"""
JD 知识库接口：录入、批量导入、列表、详情、删除
"""
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["JD知识库"])

# ── 录入单条 JD ──
@router.post("/jd", response_model=ApiResponse)
async def create_jd_api(
    req: JdCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        jd = await create_jd(db, req)
    except Exception:
        logger.exception("JD 录入失败")
        return ApiResponse(code=500, message="录入失败，请稍后重试")
    return ApiResponse.success(
        data=JdResponse.model_validate(jd).model_dump(),
        message="录入成功",
    )

# ── 批量导入 JD ──
@router.post("/jd/import", response_model=ApiResponse)
async def import_jds_api(
    req: JdImportRequest,
    db: AsyncSession = Depends(get_db),
):
    if not req.items:
        return ApiResponse(code=400, message="导入列表不能为空")
    try:
        jds = await import_jds(db, req.items)
    except Exception:
        logger.exception("JD 批量导入失败")
        return ApiResponse(code=500, message="导入失败，请稍后重试")
    return ApiResponse.success(
        data={
            "count": len(jds),
            "list": [JdListItem.model_validate(jd).model_dump() for jd in jds],
        },
        message=f"成功导入 {len(jds)} 条 JD",
    )

# ── JD 列表（分页） ──
@router.get("/jd/list", response_model=ApiResponse)
async def list_jds_api(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_jds(db, page, page_size)
    return ApiResponse.success(data={
        "list": [JdListItem.model_validate(jd).model_dump() for jd in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })

# ── JD 详情 ──
@router.get("/jd/{jd_id}", response_model=ApiResponse)
async def get_jd_api(
    jd_id: int,
    db: AsyncSession = Depends(get_db),
):
    jd = await get_jd(db, jd_id)
    if not jd:
        return ApiResponse(code=404, message="JD 不存在")
    return ApiResponse.success(data=JdResponse.model_validate(jd).model_dump())

# ── 删除 JD ──
@router.delete("/jd/{jd_id}", response_model=ApiResponse)
async def delete_jd_api(
    jd_id: int,
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_jd(db, jd_id)
    if not ok:
        return ApiResponse(code=404, message="JD 不存在")
    return ApiResponse.success(message="删除成功")
