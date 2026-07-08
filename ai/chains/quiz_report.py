import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ai.chains.utils import extract_json
from ai.model.deepseek import get_llm
from ai.prompts.quiz_report import QUIZ_REPORT_SYSTEM_PROMPT
from schemas.quiz import AIQuizReportOutput

logger = logging.getLogger(__name__)

"""
评估报告生成链：汇总答题结果，调用 DeepSeek 输出结构化评估报告 JSON
"""


# ── 生成评估报告 ──
async def generate_report(
    questions: list[dict],
    ability_profile: dict,
) -> AIQuizReportOutput:
    # 1. 汇总答题记录
    answer_records = []
    for q in questions:
        record = {
            "题目": q.get("stem", ""),
            "分类": q.get("category", ""),
            "主题标签": q.get("topic_tags", []),
            "用户答案": q.get("user_answer", "未作答"),
            "是否正确": "正确" if q.get("is_correct") else ("错误" if q.get("user_answer") else "未作答"),
        }
        answer_records.append(record)
    # 2. 构造消息（用 replace 避免 JSON 示例中的大括号被误解析）
    system_prompt = QUIZ_REPORT_SYSTEM_PROMPT.replace(
        "{ability_profile}", json.dumps(ability_profile, ensure_ascii=False, indent=2)
    )
    system_prompt = system_prompt.replace(
        "{answer_records}", json.dumps(answer_records, ensure_ascii=False, indent=2)
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="请根据以上答题记录和能力画像生成评估报告，严格按 JSON 格式输出。"),
    ]
    # 3. 获取 LLM 实例（报告用稍高温度，让建议更有创意）
    llm = get_llm(temperature=0.5)
    result = await llm.ainvoke(messages)
    # 4. 提取回复文本
    content = result.content if isinstance(result, AIMessage) else str(result)
    # 5. 手动解析 JSON
    data = extract_json(content)
    # 6. 校验并返回
    return AIQuizReportOutput.model_validate(data)
