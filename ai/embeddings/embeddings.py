from langchain_community.embeddings import DashScopeEmbeddings
from ai.config import ai_settings

"""
Embedding 模型工厂

DASHSCOPE_API_KEY 通过 ai/__init__.py 的 load_dotenv() 加载到环境变量，
DashScopeEmbeddings 会自动读取，无需显式传入。
"""
# ── 获取 Embedding 模型 ──
def get_embeddings() -> DashScopeEmbeddings:
    return DashScopeEmbeddings(model=ai_settings.DASHSCOPE_EMBEDDING_MODEL)
