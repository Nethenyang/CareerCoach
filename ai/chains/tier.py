import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ai.chains.utils import extract_json
from ai.model.deepseek import get_resume_llm
from ai.prompts.tier import TIER_SYSTEM_PROMPT
from schemas.resume import TierSuggestion

logger = logging.getLogger(__name__)

"""
梯队建议链：根据能力画像，推荐最合适的求职梯队
"""


async def suggest_tier(ability_profile: dict) -> TierSuggestion:
    # 1. 把能力画像转成 JSON 字符串作为用户消息
    profile_json = json.dumps(ability_profile, ensure_ascii=False, indent=2)
    messages = [
        SystemMessage(content=TIER_SYSTEM_PROMPT),
        HumanMessage(content=profile_json),
    ]
    # 2. 获取 LLM 实例并异步调用
    llm = get_resume_llm()
    result = await llm.ainvoke(messages)
    # 3. 提取回复文本
    content = result.content if isinstance(result, AIMessage) else str(result)
    # 4. 解析 JSON
    data = extract_json(content)
    # 5. 校验并返回
    return TierSuggestion.model_validate(data)
