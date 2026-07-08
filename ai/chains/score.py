import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ai.chains.utils import extract_json
from ai.model.deepseek import get_resume_llm
from ai.prompts.score import SCORE_SYSTEM_PROMPT
from schemas.resume import ScoreAssessment

logger = logging.getLogger(__name__)

"""
评分链：根据简历文本 + 能力画像，输出多维度量化评分
"""


async def evaluate_score(resume_text: str, ability_profile: dict) -> dict:
    # 1. 拼接用户消息内容
    profile_json = json.dumps(ability_profile, ensure_ascii=False, indent=2)
    user_content = f"## 简历文本\n{resume_text}\n\n## 能力评估结果\n{profile_json}"
    # 2. 构造消息列表
    messages = [
        SystemMessage(content=SCORE_SYSTEM_PROMPT),
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
    validated = ScoreAssessment.model_validate(data)
    return validated.model_dump()
