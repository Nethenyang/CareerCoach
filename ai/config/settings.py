from pydantic_settings import BaseSettings, SettingsConfigDict

"""
AI 模块配置
"""
class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # ── DeepSeek ──
    DEEPSEEK_MODEL: str
    DEEPSEEK_TEMPERATURE: float

    # ── Tavily 搜索 API ──
    TAVILY_API_KEY: str

    # ── 阿里云 DashScope Embedding ──
    DASHSCOPE_API_KEY: str
    DASHSCOPE_EMBEDDING_MODEL: str

ai_settings = AISettings()
