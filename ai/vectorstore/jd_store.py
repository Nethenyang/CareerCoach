import asyncio
import logging
from langchain_redis import RedisConfig, RedisVectorStore
from redisvl.query.filter import Tag
from ai.embeddings.embeddings import get_embeddings
from core.config import settings

"""
JD 向量库封装：建索引、添加、检索、删除
"""
logger = logging.getLogger(__name__)

_INDEX_NAME = "jd_knowledge"

# Redis 向量索引的 metadata 字段定义
_METADATA_SCHEMA = [
    {"name": "jd_id", "type": "numeric"},
    {"name": "tier", "type": "tag"},
    {"name": "tech_direction", "type": "tag"},
    {"name": "company", "type": "tag"},
    {"name": "position", "type": "tag"},
]

# ── 拼接 Redis 连接 URL ──
def _build_redis_url() -> str:
    if settings.REDIS_PASSWORD:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"

# 模块级单例（lazy init，首次调用时才连接 Redis 建索引）
_vector_store: RedisVectorStore | None = None

# ── 获取向量库实例（单例） ──
def _get_vector_store() -> RedisVectorStore:
    global _vector_store
    if _vector_store is None:
        config = RedisConfig(
            index_name=_INDEX_NAME,
            redis_url=_build_redis_url(),
            distance_metric="COSINE",
            metadata_schema=_METADATA_SCHEMA,
        )
        _vector_store = RedisVectorStore(embeddings=get_embeddings(), config=config)
    return _vector_store

# ── 添加单条 JD 到向量库 ──
async def add_jd(jd_id: int, requirements: str, metadata: dict) -> str:
    store = _get_vector_store()
    key = f"jd:{jd_id}"
    # 确保 metadata 含 jd_id
    full_metadata = {"jd_id": jd_id, **metadata}
    await asyncio.to_thread(
        store.add_texts,
        texts=[requirements],
        metadatas=[full_metadata],
        keys=[key],
    )
    return key

# ── 批量添加 JD ──
async def add_jds(items: list[dict]) -> list[str]:
    if not items:
        return []
    store = _get_vector_store()
    texts = [item["requirements"] for item in items]
    keys = [f"jd:{item['jd_id']}" for item in items]
    metadatas = [{"jd_id": item["jd_id"], **item["metadata"]} for item in items]
    await asyncio.to_thread(
        store.add_texts,
        texts=texts,
        metadatas=metadatas,
        keys=keys,
    )
    return keys

# ── 语义检索 JD（支持 tier 过滤） ──
async def search_jds(
    query: str,
    tiers: list[str] | None = None,
    k: int = 5,
) -> list[dict]:
    store = _get_vector_store()
    # 构造 metadata 过滤条件
    filter_expr = None
    if tiers:
        filter_expr = Tag("tier") == tiers

    results = await asyncio.to_thread(
        store.similarity_search_with_score,
        query,
        k=k,
        filter=filter_expr,
    )

    output = []
    for doc, score in results:
        output.append({
            "jd_id": int(doc.metadata.get("jd_id", 0)),
            "score": float(score),
            "company": doc.metadata.get("company", ""),
            "position": doc.metadata.get("position", ""),
            "tier": doc.metadata.get("tier", ""),
            "tech_direction": doc.metadata.get("tech_direction", ""),
            "requirements": doc.page_content,
        })
    return output

# ── 删除单条 JD 向量 ──
async def delete_jd(jd_id: int) -> None:
    # 按 jd_id 删除对应的向量
    store = _get_vector_store()
    key = f"jd:{jd_id}"
    await asyncio.to_thread(store.delete, [key])

# ── 删除整个索引（管理/重建用） ──
async def drop_index() -> None:
    # 删除 jd_knowledge 向量索引（谨慎使用，管理功能）
    global _vector_store
    if _vector_store is not None:
        try:
            await asyncio.to_thread(_vector_store.drop_index)
        except AttributeError:
            logger.warning("RedisVectorStore 无 drop_index 方法，跳过索引删除")
        _vector_store = None
