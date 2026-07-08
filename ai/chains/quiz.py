import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ai.chains.utils import extract_json
from ai.model.deepseek import get_resume_llm
from ai.prompts.quiz import build_quiz_prompt
from schemas.quiz import AIQuizGenerateOutput

logger = logging.getLogger(__name__)

"""
面试题生成链：调用 DeepSeek 输出结构化选择题 JSON
注意：DeepSeek 不支持 LangChain 的 with_structured_output（function calling），
改为直接调用 LLM，手动解析 JSON 响应。
"""


# ── 生成测验题目 ──
async def generate_quiz(
    target_jd: str,
    ability_profile: dict,
    suggestions: list[dict],
    question_count: int,
    user_requirements: str,
) -> AIQuizGenerateOutput:
    # 1. 构造系统提示词和用户消息
    system_prompt, user_prompt = build_quiz_prompt(
        target_jd=target_jd,
        ability_profile=ability_profile,
        suggestions=suggestions,
        question_count=question_count,
        user_requirements=user_requirements,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    # 2. 获取 LLM 实例并异步调用
    llm = get_resume_llm()
    result = await llm.ainvoke(messages)
    # 3. 提取回复文本
    content = result.content if isinstance(result, AIMessage) else str(result)
    # 4. 手动解析 JSON（DeepSeek 不支持 function calling）
    data = extract_json(content)
    # 5. 校验并返回 Pydantic 对象
    return AIQuizGenerateOutput.model_validate(data)
