from typing import Optional
from sqlalchemy import delete as sql_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.conversation import Conversation
from models.message import Message
from models.resume import Resume

"""
对话业务逻辑：创建、列表、详情、重命名、删除
每条对话必须绑定一个简历分析结果。
"""
# ── 创建对话（绑定简历，幂等：同一简历已存在对话则直接返回） ──
async def create_conversation(db: AsyncSession, user_id: int, resume_id: int, title: str = "") -> Conversation:
    # 幂等：同一简历已创建过对话则直接返回，避免重复创建
    existing = await get_conversation_by_resume_id(db, user_id, resume_id)
    if existing:
        return existing
    # 未提供标题时，从简历文件名自动生成
    if not title:
        result = await db.execute(select(Resume.filename).where(Resume.id == resume_id))
        filename = result.scalar_one_or_none() or "未命名"
        title = f"简历分析 - {filename}"
    conv = Conversation(user_id=user_id, resume_id=resume_id, title=title)
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv

# ── 查询用户对话列表（按更新时间倒序，JOIN 简历获取文件名） ──
async def list_conversations(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
    count_query = select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Conversation, Resume.filename)
        .outerjoin(Resume, Conversation.resume_id == Resume.id)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.all()

    items = [
        {
            "id": conv.id,
            "title": conv.title,
            "resume_id": conv.resume_id,
            "resume_filename": filename,
            "message_count": conv.message_count,
            "last_message_at": conv.last_message_at,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        }
        for conv, filename in rows
    ]
    return items, total

# ── 按 resume_id 查询关联对话（取最近一条，用于判断是否已创建） ──
async def get_conversation_by_resume_id(db: AsyncSession, user_id: int, resume_id: int) -> Optional[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.resume_id == resume_id)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

# ── 根据 ID 查询对话 ──
async def get_conversation_by_id(db: AsyncSession, conversation_id: int) -> Optional[Conversation]:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    return result.scalar_one_or_none()

# ── 重命名对话 ──
async def rename_conversation(db: AsyncSession, conversation_id: int, title: str) -> Optional[Conversation]:
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        return None
    conv.title = title
    await db.flush()
    await db.refresh(conv)
    return conv

# ── 删除对话（级联删除消息） ──
async def delete_conversation(db: AsyncSession, conversation_id: int) -> bool:
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        return False
    await db.execute(sql_delete(Message).where(Message.conversation_id == conversation_id))
    await db.delete(conv)
    await db.flush()
    return True
