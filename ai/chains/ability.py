import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ai.chains.utils import extract_json
from ai.model.deepseek import get_resume_llm
from ai.prompts.ability import ABILITY_SYSTEM_PROMPT
from schemas.resume import AbilityProfile

logger = logging.getLogger(__name__)

"""
能力评估链：根据简历文本 + 优化建议，输出结构化能力画像
"""


async def evaluate_ability(resume_text: str, suggestions: list[dict]) -> AbilityProfile:
    # 1. 拼接用户消息内容
    suggestions_json = json.dumps(suggestions, ensure_ascii=False, indent=2)
    user_content = f"## 简历文本\n{resume_text}\n\n## 简历优化建议\n{suggestions_json}"
    # 2. 构造消息列表
    messages = [
        SystemMessage(content=ABILITY_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    # 3. 获取 LLM 实例并异步调用
    llm = get_resume_llm()
    result = await llm.ainvoke(messages)
    # 4. 提取回复文本
    content = result.content if isinstance(result, AIMessage) else str(result)
    # 5. 解析 JSON
    data = extract_json(content)
    # 6. 校验并返回
    return AbilityProfile.model_validate(data)
