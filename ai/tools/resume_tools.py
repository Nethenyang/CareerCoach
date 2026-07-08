import json
import logging
from langchain_core.tools import tool
from core.database import async_session_factory
from services.resume import get_resume_by_id

"""
简历相关工具：Agent 可调用
"""
logger = logging.getLogger(__name__)


@tool
async def get_resume_analysis(resume_id: int) -> str:
    """获取指定简历的完整分析结果，包含所有优化建议。在对话开始时调用此工具以了解简历上下文。

    Args:
        resume_id: 简历 ID（整数）
    """
    try:
        async with async_session_factory() as db:
            resume = await get_resume_by_id(db, resume_id)
            if not resume:
                return "简历不存在"
            if not resume.suggestions:
                return "该简历尚未完成分析"
            return json.dumps(
                {
                    "filename": resume.filename,
                    "total_issues": resume.total_issues,
                    "suggestions": resume.suggestions,
                },
                ensure_ascii=False,
            )
    except Exception as e:
        logger.exception("get_resume_analysis 工具调用失败: resume_id=%s", resume_id)
        return f"获取简历分析结果失败: {e}"
