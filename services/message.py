import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.message import Message
from models.conversation import Conversation
from services.resume import get_resume_by_id
from ai.agents.career_coach import get_career_coach_agent

"""
消息业务逻辑：发送消息、查询历史
"""

# 对话历史最大条数（滑动窗口，超出则丢弃最老的消息）
HISTORY_LIMIT = 20


# ── 获取对话的所有消息（时间正序） ──
async def get_messages(db: AsyncSession, conversation_id: int) -> list[Message]:
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


# ── 加载最近 N 条历史消息（排除指定消息，时间正序） ──
async def _load_history(db: AsyncSession, conversation_id: int, exclude_id: int) -> list[dict]:
    # 1. 查最近 N 条（倒序），排除刚保存的用户消息
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.id != exclude_id)
        .order_by(Message.created_at.desc())
        .limit(HISTORY_LIMIT)
    )
    rows = list(result.scalars().all())
    # 2. 反转为正序（最老→最新）
    rows.reverse()
    # 3. 转成 Agent 需要的 dict 格式
    history = []
    for msg in rows:
        history.append({"role": msg.role, "content": msg.content})
    return history


# ── 从 Agent 响应中提取 token 用量 ──
def _extract_token_usage(last_msg) -> tuple[int | None, int | None]:
    # 1. 优先用 LangChain 标准化的 usage_metadata
    if hasattr(last_msg, "usage_metadata") and last_msg.usage_metadata:
        input_tokens = last_msg.usage_metadata.get("input_tokens")
        output_tokens = last_msg.usage_metadata.get("output_tokens")
        return input_tokens, output_tokens
    # 2. 回退到 response_metadata.token_usage（OpenAI 兼容格式）
    if hasattr(last_msg, "response_metadata"):
        token_usage = last_msg.response_metadata.get("token_usage", {})
        prompt_tokens = token_usage.get("prompt_tokens")
        completion_tokens = token_usage.get("completion_tokens")
        return prompt_tokens, completion_tokens
    # 3. 都没有就返回 None
    return None, None


# ── 发送消息并获取 AI 回复 ──
async def send_message(db: AsyncSession, conversation_id: int, content: str) -> dict:
    now = datetime.now()

    # 1. 保存用户消息
    user_msg = Message(conversation_id=conversation_id, role="user", content=content)
    db.add(user_msg)
    await db.flush()
    await db.refresh(user_msg)

    # 2. 获取对话关联的简历
    conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = conv_result.scalar_one_or_none()
    resume_id = conv.resume_id if conv else None

    # 3. 从 DB 加载简历分析结果，拼成上下文字符串
    analysis_context = ""
    if resume_id:
        resume = await get_resume_by_id(db, resume_id)
        if resume and resume.suggestions:
            analysis_data = {
                "filename": resume.filename,
                "total_issues": resume.total_issues,
                "suggestions": resume.suggestions,
            }
            analysis_context = json.dumps(analysis_data, ensure_ascii=False)

    # 4. 加载对话历史（滑动窗口，排除刚保存的用户消息）
    history = await _load_history(db, conversation_id, user_msg.id)

    # 5. 构造完整消息列表：system + 历史 + 当前用户消息
    system_msg = {
        "role": "system",
        "content": f"以下是用户的简历分析结果，请基于此回答用户问题：\n{analysis_context}",
    }
    current_user_msg = {"role": "user", "content": content}
    messages = [system_msg]
    messages.extend(history)
    messages.append(current_user_msg)

    # 6. 调用 Agent（自动处理 tool calling 循环）
    agent = get_career_coach_agent()
    result = await agent.ainvoke({"messages": messages})

    # 7. 提取 AI 回复（最后一条消息）
    last_msg = result["messages"][-1]
    ai_content = last_msg.content
    # 如果 content 是 list（多段文本），拼成纯字符串
    if isinstance(ai_content, list):
        parts = []
        for part in ai_content:
            text = part.get("text", "") if isinstance(part, dict) else str(part)
            parts.append(text)
        ai_content = "".join(parts)

    # 8. 提取 token 用量
    prompt_tokens, completion_tokens = _extract_token_usage(last_msg)

    # 9. 保存 AI 回复（含 token 用量）
    ai_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    db.add(ai_msg)
    await db.flush()
    await db.refresh(ai_msg)

    # 10. 更新对话统计
    conv.message_count = (conv.message_count or 0) + 2
    conv.last_message_at = now
    await db.flush()

    return {"user_message": user_msg, "ai_message": ai_msg}


# ── 流式发送消息，返回 SSE 事件流 ──
async def send_message_stream(db: AsyncSession, conversation_id: int, content: str):
    """async generator，逐 token yield JSON 字符串，最后 yield done 事件"""
    now = datetime.now()
    import logging
    logger = logging.getLogger(__name__)

    try:
        # 1. 保存用户消息
        user_msg = Message(conversation_id=conversation_id, role="user", content=content)
        db.add(user_msg)
        await db.flush()
        await db.refresh(user_msg)

        # 2. 获取对话关联的简历
        conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conv = conv_result.scalar_one_or_none()
        resume_id = conv.resume_id if conv else None

        # 3. 从 DB 加载简历分析结果
        analysis_context = ""
        if resume_id:
            resume = await get_resume_by_id(db, resume_id)
            if resume and resume.suggestions:
                analysis_data = {
                    "filename": resume.filename,
                    "total_issues": resume.total_issues,
                    "suggestions": resume.suggestions,
                }
                analysis_context = json.dumps(analysis_data, ensure_ascii=False)

        # 4. 加载对话历史
        history = await _load_history(db, conversation_id, user_msg.id)

        # 5. 构造消息列表
        system_msg = {
            "role": "system",
            "content": f"以下是用户的简历分析结果，请基于此回答用户问题：\n{analysis_context}",
        }
        messages = [system_msg]
        messages.extend(history)
        messages.append({"role": "user", "content": content})

        # 6. 流式调用 Agent
        agent = get_career_coach_agent()
        full_content = ""
        prompt_tokens = None
        completion_tokens = None

        async for event in agent.astream_events({"messages": messages}, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # 只流式输出文本内容，跳过 tool_call 的 JSON 片段
                if chunk.content and isinstance(chunk.content, str):
                    full_content += chunk.content
                    yield "data: " + json.dumps({"type": "token", "content": chunk.content}, ensure_ascii=False) + "\n\n"
            elif event["event"] == "on_chat_model_end":
                # 提取最后的 token 用量（可能是多轮 LLM 调用，取最后一次）
                output = event["data"].get("output", {})
                if hasattr(output, "usage_metadata") and output.usage_metadata:
                    prompt_tokens = output.usage_metadata.get("input_tokens")
                    completion_tokens = output.usage_metadata.get("output_tokens")

        # 7. 保存 AI 回复
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        db.add(ai_msg)
        await db.flush()
        await db.refresh(ai_msg)

        # 8. 更新对话统计
        conv.message_count = (conv.message_count or 0) + 2
        conv.last_message_at = now
        await db.flush()

        # 9. 发送完成事件（含消息 ID）
        yield "data: " + json.dumps({
            "type": "done",
            "message_id": ai_msg.id,
            "user_message_id": user_msg.id,
            "created_at": ai_msg.created_at.isoformat(),
        }, ensure_ascii=False, default=str) + "\n\n"

    except Exception as e:
        logger.exception("流式消息生成失败")
        yield "data: " + json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False) + "\n\n"
