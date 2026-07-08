from langchain.chat_models import init_chat_model
from ai.config import ai_settings

"""
DeepSeek 大模型初始化
"""
# ── 简历分析模型（低温度，稳定输出） ──
def get_resume_llm():
    return init_chat_model(
        model=ai_settings.DEEPSEEK_MODEL,
        temperature=ai_settings.DEEPSEEK_TEMPERATURE,
    )

# ── 通用模型 ──
def get_default_llm():
    return init_chat_model(
        model=ai_settings.DEEPSEEK_MODEL,
        temperature=0.7,
    )

# ── 自定义温度 ──
def get_llm(temperature: float = 0.7):
    return init_chat_model(
        model=ai_settings.DEEPSEEK_MODEL,
        temperature=temperature,
    )
