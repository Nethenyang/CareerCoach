from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from middleware.auth import get_current_user_id
from schemas.response import ApiResponse
from schemas.conversation import (
    ConversationResponse,
    CreateConversationRequest,
    MessageListResponse,
    MessageResponse,
    RenameRequest,
    SendMessageRequest,
    SendMessageResponse,
)
from services.conversation import (
    create_conversation,
    delete_conversation,
    get_conversation_by_id,
    list_conversations,
    rename_conversation,
)
from services.message import get_messages, send_message, send_message_stream
from services.resume import get_resume_by_id

"""
对话接口：新建、消息、列表、历史、重命名、删除
每条对话必须绑定一个简历分析结果。
"""
router = APIRouter(prefix="/api/conversation", tags=["对话"])

# ── 新建对话（绑定简历） ──
@router.post("/create", response_model=ApiResponse)
async def create(
    req: CreateConversationRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # 校验简历归属
    resume = await get_resume_by_id(db, req.resume_id)
    if not resume:
        return ApiResponse(code=404, message="简历不存在")
    if resume.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该简历")

    conv = await create_conversation(db, user_id, req.resume_id, req.title or "")
    return ApiResponse.success(
        data=ConversationResponse.model_validate(conv).model_dump(),
        message="创建成功",
    )

# ── 发送消息 ──
@router.post("/message/{conversation_id}", response_model=ApiResponse)
async def send_msg(
    conversation_id: int,
    req: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        return ApiResponse(code=404, message="对话不存在")
    if conv.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该对话")

    result = await send_message(db, conversation_id, req.content)
    return ApiResponse.success(data={
        "user_message": MessageResponse.model_validate(result["user_message"]).model_dump(),
        "ai_message": MessageResponse.model_validate(result["ai_message"]).model_dump(),
    })

# ── 流式发送消息 ──
@router.post("/message/{conversation_id}/stream")
async def send_msg_stream(
    conversation_id: int,
    req: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        return ApiResponse(code=404, message="对话不存在")
    if conv.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该对话")

    return StreamingResponse(
        send_message_stream(db, conversation_id, req.content),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )

# ── 对话列表 ──
@router.get("/list", response_model=ApiResponse)
async def list_view(
    page: int = 1,
    page_size: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_conversations(db, user_id, page, page_size)
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    })

# ── 对话历史消息 ──
@router.get("/messages/{conversation_id}", response_model=ApiResponse)
async def history(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        return ApiResponse(code=404, message="对话不存在")
    if conv.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该对话")

    messages = await get_messages(db, conversation_id)
    return ApiResponse.success(data={
        "conversation_id": conversation_id,
        "title": conv.title,
        "messages": [MessageResponse.model_validate(m).model_dump() for m in messages],
    })

# ── 重命名对话 ──
@router.put("/rename/{conversation_id}", response_model=ApiResponse)
async def rename(
    conversation_id: int,
    req: RenameRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        return ApiResponse(code=404, message="对话不存在")
    if conv.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该对话")

    updated = await rename_conversation(db, conversation_id, req.title)
    return ApiResponse.success(
        data=ConversationResponse.model_validate(updated).model_dump(),
        message="重命名成功",
    )

# ── 删除对话 ──
@router.delete("/{conversation_id}", response_model=ApiResponse)
async def delete(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        return ApiResponse(code=404, message="对话不存在")
    if conv.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该对话")

    await delete_conversation(db, conversation_id)
    return ApiResponse.success(message="删除成功")
