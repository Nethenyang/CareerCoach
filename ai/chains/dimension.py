import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ai.chains.utils import extract_json
from ai.model.deepseek import get_resume_llm
from ai.prompts.dimension import DIMENSION_SYSTEM_PROMPT, STRATEGIC_SYSTEM_PROMPT
from schemas.resume import DimensionScore, StrategicSuggestion

logger = logging.getLogger(__name__)

"""
维度分析链：评估简历文档质量（4固定维度+子项）+ 战略建议
"""


async def evaluate_dimensions(resume_text: str) -> dict:
    # 1. 构造用户消息
    user_content = f"## 简历文本\n{resume_text}"
    # 2. 构造消息列表
    messages = [
        SystemMessage(content=DIMENSION_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    # 3. 获取 LLM 实例并异步调用
    llm = get_resume_llm()
    result = await llm.ainvoke(messages)
    # 4. 提取回复文本
    content = result.content if isinstance(result, AIMessage) else str(result)
    # 5. 解析 JSON
    data = extract_json(content)
    # 6. 逐个校验维度（LLM 只返回 dimensions，不返回 strategic_suggestions）
    dimensions_list = []
    for d in data["dimensions"]:
        validated = DimensionScore.model_validate(d)
        dimensions_list.append(validated.model_dump())
    # 7. 返回
    return {"dimensions": dimensions_list}


async def evaluate_strategic_suggestions(resume_text: str, ability_profile: dict) -> dict:
    # 1. 把能力画像转成 JSON 字符串
    profile_json = json.dumps(ability_profile, ensure_ascii=False, indent=2)
    # 2. 构造用户消息
    user_content = f"## 简历文本\n{resume_text}\n\n## 能力评估结果\n{profile_json}"
    # 3. 构造消息列表
    messages = [
        SystemMessage(content=STRATEGIC_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    # 4. 获取 LLM 实例并异步调用
    llm = get_resume_llm()
    result = await llm.ainvoke(messages)
    # 5. 提取回复文本
    content = result.content if isinstance(result, AIMessage) else str(result)
    # 6. 解析 JSON
    data = extract_json(content)
    # 7. 逐个校验战略建议（LLM 只返回 strategic_suggestions，不返回 dimensions）
    suggestions_list = []
    for s in data["strategic_suggestions"]:
        validated = StrategicSuggestion.model_validate(s)
        suggestions_list.append(validated.model_dump())
    # 8. 返回
    return {"strategic_suggestions": suggestions_list}
