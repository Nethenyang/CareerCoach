import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.jd import JdKnowledge
from schemas.jd import JdCreateRequest
from ai.vectorstore.jd_store import add_jd, add_jds, delete_jd as delete_jd_vector

"""
JD 知识库业务逻辑：录入、批量导入、列表、详情、删除

JD 知识库是全局共享的（jd_knowledge 无 user_id），不做归属校验。
向量化失败不阻断入库，vector_indexed 保持 0。
"""
logger = logging.getLogger(__name__)

# ── 录入单条 JD：入库 → 向量化 → 更新 vector_indexed ──
async def create_jd(db: AsyncSession, data: JdCreateRequest) -> JdKnowledge:
    jd = JdKnowledge(
        company=data.company,
        position=data.position,
        tier=data.tier,
        tech_direction=data.tech_direction,
        requirements=data.requirements,
        source_url=data.source_url,
    )
    db.add(jd)
    await db.flush()
    await db.refresh(jd)  # 拿到 id 和 created_at

    # 向量化（失败不阻断入库）
    metadata = {
        "tier": data.tier,
        "tech_direction": data.tech_direction,
        "company": data.company,
        "position": data.position,
    }
    try:
        await add_jd(jd.id, data.requirements, metadata)
        jd.vector_indexed = 1
    except Exception:
        logger.exception("JD 向量化失败 jd_id=%s", jd.id)
    await db.flush()
    await db.refresh(jd)
    return jd

# ── 批量导入 ──
async def import_jds(db: AsyncSession, items: list[JdCreateRequest]) -> list[JdKnowledge]:
    jd_list = [
        JdKnowledge(
            company=item.company,
            position=item.position,
            tier=item.tier,
            tech_direction=item.tech_direction,
            requirements=item.requirements,
            source_url=item.source_url,
        )
        for item in items
    ]
    db.add_all(jd_list)
    await db.flush()  # 拿到所有 id

    # 批量向量化（失败不阻断入库，全部保持 vector_indexed=0）
    store_items = [
        {
            "jd_id": jd.id,
            "requirements": jd.requirements,
            "metadata": {
                "tier": jd.tier,
                "tech_direction": jd.tech_direction,
                "company": jd.company,
                "position": jd.position,
            },
        }
        for jd in jd_list
    ]
    try:
        await add_jds(store_items)
        for jd in jd_list:
            jd.vector_indexed = 1
    except Exception:
        logger.exception("批量 JD 向量化失败")
    await db.flush()
    # refresh 加载 server_default 生成的字段（如 created_at），避免异步懒加载报错
    for jd in jd_list:
        await db.refresh(jd)
    return jd_list

# ── 分页列表（按 created_at 倒序） ──
async def list_jds(db: AsyncSession, page: int = 1, page_size: int = 10) -> tuple[list[JdKnowledge], int]:
    count_query = select(func.count()).select_from(JdKnowledge)
    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = (
        select(JdKnowledge)
        .order_by(JdKnowledge.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total

# ── 详情 ──
async def get_jd(db: AsyncSession, jd_id: int) -> Optional[JdKnowledge]:
    result = await db.execute(select(JdKnowledge).where(JdKnowledge.id == jd_id))
    return result.scalar_one_or_none()

# ── 删除（MySQL 记录 + 向量库向量） ──
async def delete_jd(db: AsyncSession, jd_id: int) -> bool:
    jd = await get_jd(db, jd_id)
    if not jd:
        return False
    # 删向量（不阻断 MySQL 删除）
    if jd.vector_indexed:
        try:
            await delete_jd_vector(jd.id)
        except Exception:
            logger.exception("删除 JD 向量失败 jd_id=%s", jd_id)
    await db.delete(jd)
    await db.flush()
    return True
