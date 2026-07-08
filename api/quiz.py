import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from middleware.auth import get_current_user_id
from schemas.response import ApiResponse

logger = logging.getLogger(__name__)
from schemas.quiz import (
    AnswerQuestionRequest,
    AnswerQuestionResponse,
    CreateQuizRequest,
    CreateQuizResponse,
    QuizDetailResponse,
    QuizListItem,
    QuizSessionResponse,
    QuizQuestionResponse,
)
from services.quiz import (
    answer_question,
    create_quiz_session,
    delete_quiz_session,
    finish_quiz,
    get_quiz_questions,
    get_quiz_session,
    list_quiz_sessions,
    reset_quiz_session,
)

"""
测验接口：创建、作答、结束、列表、详情、删除
"""
router = APIRouter(prefix="/api/quiz", tags=["测验"])


# ── 创建测验 + AI 生成题目 ──
@router.post("/create", response_model=ApiResponse)
async def create(
    req: CreateQuizRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        session, questions = await create_quiz_session(
            db=db,
            user_id=user_id,
            conversation_id=req.conversation_id,
            title=req.title,
            question_count=req.question_count,
            user_requirements=req.user_requirements or "",
        )
    except Exception:
        logger.exception("创建测验失败 user_id=%s conversation_id=%s", user_id, req.conversation_id)
        return ApiResponse(code=500, message="AI 生成题目失败，请稍后重试")

    return ApiResponse.success(
        data=CreateQuizResponse(
            session=QuizSessionResponse.model_validate(session),
            questions=[QuizQuestionResponse.model_validate(q) for q in questions],
        ).model_dump(),
        message="测验创建成功",
    )


# ── 提交单题答案 ──
@router.post("/answer/{session_id}", response_model=ApiResponse)
async def answer(
    session_id: int,
    req: AnswerQuestionRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await get_quiz_session(db, session_id)
    if not session:
        return ApiResponse(code=404, message="测验不存在")
    if session.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该测验")
    if session.status == "completed":
        return ApiResponse(code=422, message="测验已结束，无法作答")

    try:
        result = await answer_question(db, session_id, req.question_id, req.selected_option_id)
    except ValueError as e:
        return ApiResponse(code=404, message=str(e))

    return ApiResponse.success(data=AnswerQuestionResponse(**result).model_dump())


# ── 结束测验并生成报告 ──
@router.post("/finish/{session_id}", response_model=ApiResponse)
async def finish(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await get_quiz_session(db, session_id)
    if not session:
        return ApiResponse(code=404, message="测验不存在")
    if session.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该测验")

    try:
        report = await finish_quiz(db, session_id)
    except ValueError as e:
        return ApiResponse(code=422, message=str(e))

    return ApiResponse.success(data=report.model_dump(), message="报告生成完成")


# ── 重置测验（清空答案和报告，重新答题） ──
@router.post("/reset/{session_id}", response_model=ApiResponse)
async def reset(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await get_quiz_session(db, session_id)
    if not session:
        return ApiResponse(code=404, message="测验不存在")
    if session.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该测验")

    try:
        session = await reset_quiz_session(db, session_id)
    except ValueError as e:
        return ApiResponse(code=422, message=str(e))
    except Exception:
        logger.exception("重置测验失败 session_id=%s", session_id)
        return ApiResponse(code=500, message="重置失败，请稍后重试")

    questions = await get_quiz_questions(db, session_id)
    return ApiResponse.success(
        data=QuizDetailResponse(
            session=QuizSessionResponse.model_validate(session),
            questions=[QuizQuestionResponse.model_validate(q) for q in questions],
        ).model_dump(),
        message="测验已重置",
    )


# ── 测验历史列表 ──
@router.get("/list", response_model=ApiResponse)
async def list_view(
    conversation_id: int = Query(..., description="对话 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页条数"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_quiz_sessions(db, conversation_id, page, page_size)
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [QuizListItem(**item).model_dump() for item in items],
    })


# ── 测验详情 ──
@router.get("/{session_id}", response_model=ApiResponse)
async def detail(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await get_quiz_session(db, session_id)
    if not session:
        return ApiResponse(code=404, message="测验不存在")
    if session.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该测验")

    questions = await get_quiz_questions(db, session_id)
    return ApiResponse.success(data=QuizDetailResponse(
        session=QuizSessionResponse.model_validate(session),
        questions=[QuizQuestionResponse.model_validate(q) for q in questions],
    ).model_dump())


# ── 删除测验 ──
@router.delete("/{session_id}", response_model=ApiResponse)
async def delete(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await get_quiz_session(db, session_id)
    if not session:
        return ApiResponse(code=404, message="测验不存在")
    if session.user_id != user_id:
        return ApiResponse(code=403, message="无权访问该测验")

    await delete_quiz_session(db, session_id)
    return ApiResponse.success(message="删除成功")
