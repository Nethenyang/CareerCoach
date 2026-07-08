from langchain.agents import create_agent
from ai.model.deepseek import get_default_llm
from ai.tools.jd_tools import search_jd
from ai.tools.search_tools import web_search
from ai.prompts.chat import CAREER_COACH_SYSTEM_PROMPT

"""
简历教练 Agent

使用 langchain create_agent 创建 ReAct 风格 Agent，
自动处理工具调用循环（tool calling loop）。
Agent 无状态，对话历史由调用方（send_message）从 DB 加载后注入。
简历分析结果也由调用方直接注入 system message，无需工具获取。
"""

# ── Agent 单例（惰性初始化，避免重复创建） ──
_agent = None

def get_career_coach_agent():
    global _agent
    if _agent is None:
        # 1. 获取 LLM 实例
        llm = get_default_llm()
        # 2. 创建 Agent（绑定工具和系统提示词）
        _agent = create_agent(
            model=llm,
            tools=[search_jd, web_search],
            system_prompt=CAREER_COACH_SYSTEM_PROMPT,
        )
    return _agent
