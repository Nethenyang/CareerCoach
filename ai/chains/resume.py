import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ai.chains.utils import extract_json
from ai.model.deepseek import get_resume_llm
from ai.prompts.resume import RESUME_SYSTEM_PROMPT, build_user_prompt
from schemas.resume import ResumeAnalysis

logger = logging.getLogger(__name__)

"""
简历分析链：调用 DeepSeek 输出 4 维度结构化建议
注意：DeepSeek 不支持 LangChain 的 with_structured_output（function calling），
改为直接调用 LLM，手动解析 JSON 响应。
"""

# ── 分析简历 ──
async def analyze_resume(resume_text: str, target_jd: str = "") -> ResumeAnalysis:
    # 1. 构造用户消息（系统提示词 + 用户输入）
    user_prompt = build_user_prompt(resume_text, target_jd)
    messages = [
        SystemMessage(content=RESUME_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    # 2. 获取 LLM 实例并异步调用
    llm = get_resume_llm()
    result = await llm.ainvoke(messages)
    # 3. 提取回复文本
    content = result.content if isinstance(result, AIMessage) else str(result)
    # 4. 手动解析 JSON（DeepSeek 不支持 with_structured_output）
    data = extract_json(content)
    # 5. 校验并返回 Pydantic 对象
    return ResumeAnalysis.model_validate(data)
