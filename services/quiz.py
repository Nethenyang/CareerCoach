import logging
from sqlalchemy import delete as sql_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.conversation import Conversation
from models.quiz import QuizSession, QuizQuestion
from models.resume import Resume
from ai.chains.quiz import generate_quiz
from ai.chains.quiz_report import generate_report
from schemas.quiz import AIQuizReportOutput

logger = logging.getLogger(__name__)

"""
测验业务逻辑：创建、作答、结束、列表、详情、删除
"""


# ── 创建测验会话 + AI 生成题目 ──
async def create_quiz_session(
    db: AsyncSession,
    user_id: int,
    conversation_id: int,
    title: str,
    question_count: int,
    user_requirements: str,
) -> tuple[QuizSession, list[QuizQuestion]]:
    # 1. 查对话关联的简历
    conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = conv_result.scalar_one_or_none()
    resume_id = conv.resume_id if conv else None
    # 2. 查简历分析结果
    target_jd = ""
    ability_profile = {}
    suggestions = []
    if resume_id:
        resume_result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = resume_result.scalar_one_or_none()
        if resume:
            target_jd = resume.target_jd or ""
            ability_profile = resume.ability_profile or {}
            suggestions = resume.suggestions or []
    # 3. 调用 AI 生成题目
    ai_output = await generate_quiz(
        target_jd=target_jd,
        ability_profile=ability_profile,
        suggestions=suggestions,
        question_count=question_count,
        user_requirements=user_requirements or "",
    )
    # 4. 创建测验会话
    session = QuizSession(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title,
        target_jd=target_jd or None,
        question_count=question_count,
        user_requirements=user_requirements or None,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    # 5. 批量插入题目
    questions = []
    for i, q in enumerate(ai_output.questions):
        question = QuizQuestion(
            session_id=session.id,
            stem=q.stem,
            options=[opt.model_dump() for opt in q.options],
            correct_option_id=q.correct_option_id,
            explanation=q.explanation,
            topic_tags=q.topic_tags,
            category=q.category,
            order_index=i + 1,
        )
        db.add(question)
        questions.append(question)
    await db.flush()
    for q in questions:
        await db.refresh(q)
    return session, questions


# ── 提交单题答案 ──
async def answer_question(
    db: AsyncSession,
    session_id: int,
    question_id: int,
    selected_option_id: str,
) -> dict:
    # 查题目，校验归属
    result = await db.execute(
        select(QuizQuestion).where(
            QuizQuestion.id == question_id,
            QuizQuestion.session_id == session_id,
        )
    )
    question = result.scalar_one_or_none()
    if not question:
        raise ValueError("题目不存在或不属于该测验")
    # 判题
    is_correct = selected_option_id == question.correct_option_id
    question.user_answer = selected_option_id
    question.is_correct = is_correct
    await db.flush()
    return {
        "is_correct": is_correct,
        "correct_option_id": question.correct_option_id,
        "explanation": question.explanation,
    }


# ── 结束测验并生成报告 ──
async def finish_quiz(db: AsyncSession, session_id: int) -> AIQuizReportOutput:
    # 1. 查会话
    session_result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise ValueError("测验不存在")
    if session.status == "completed":
        raise ValueError("测验已完成")
    # 2. 查所有题目
    questions_result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.session_id == session_id)
        .order_by(QuizQuestion.order_index.asc())
    )
    questions = list(questions_result.scalars().all())
    # 3. 计算得分
    correct_count = sum(1 for q in questions if q.is_correct)
    # 4. 查能力画像（用于报告）
    conv_result = await db.execute(select(Conversation).where(Conversation.id == session.conversation_id))
    conv = conv_result.scalar_one_or_none()
    ability_profile = {}
    if conv and conv.resume_id:
        resume_result = await db.execute(select(Resume).where(Resume.id == conv.resume_id))
        resume = resume_result.scalar_one_or_none()
        if resume:
            ability_profile = resume.ability_profile or {}
    # 5. 调 AI 生成报告
    questions_dicts = [
        {
            "stem": q.stem,
            "category": q.category,
            "topic_tags": q.topic_tags,
            "user_answer": q.user_answer,
            "is_correct": q.is_correct,
        }
        for q in questions
    ]
    report = await generate_report(questions=questions_dicts, ability_profile=ability_profile)
    # 6. 更新会话
    session.score = correct_count
    session.report = report.model_dump()
    session.status = "completed"
    await db.flush()
    return report


# ── 重置测验（清除答案、分数、报告，恢复 in_progress） ──
async def reset_quiz_session(db: AsyncSession, session_id: int) -> QuizSession:
    session = await get_quiz_session(db, session_id)
    if not session:
        raise ValueError("测验不存在")
    questions = await get_quiz_questions(db, session_id)
    for q in questions:
        q.user_answer = None
        q.is_correct = None
    session.score = None
    session.report = None
    session.status = "in_progress"
    await db.flush()
    await db.refresh(session)
    return session


# ── 测验列表（按对话 ID 过滤，分页） ──
async def list_quiz_sessions(
    db: AsyncSession,
    conversation_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    count_query = select(func.count()).select_from(QuizSession).where(
        QuizSession.conversation_id == conversation_id
    )
    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = (
        select(QuizSession)
        .where(QuizSession.conversation_id == conversation_id)
        .order_by(QuizSession.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    sessions = list(result.scalars().all())
    items = [
        {
            "id": s.id,
            "title": s.title,
            "question_count": s.question_count,
            "status": s.status,
            "score": s.score,
            "created_at": s.created_at,
        }
        for s in sessions
    ]
    return items, total


# ── 测验详情（含所有题目） ──
async def get_quiz_session(db: AsyncSession, session_id: int) -> QuizSession | None:
    result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    return result.scalar_one_or_none()


# ── 获取测验的所有题目（按序号排序） ──
async def get_quiz_questions(db: AsyncSession, session_id: int) -> list[QuizQuestion]:
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.session_id == session_id)
        .order_by(QuizQuestion.order_index.asc())
    )
    return list(result.scalars().all())


# ── 删除测验（应用层级联：先删题目再删会话） ──
async def delete_quiz_session(db: AsyncSession, session_id: int) -> bool:
    session = await get_quiz_session(db, session_id)
    if not session:
        return False
    await db.execute(sql_delete(QuizQuestion).where(QuizQuestion.session_id == session_id))
    await db.delete(session)
    await db.flush()
    return True
