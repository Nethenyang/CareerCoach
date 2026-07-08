import json
import logging
from langchain_core.tools import tool
from ai.vectorstore.jd_store import search_jds

"""
JD 知识库检索工具：Agent 可调用
"""
logger = logging.getLogger(__name__)


@tool
async def search_jd(query: str, k: int = 5) -> str:
    """从 JD 知识库中语义检索相关岗位描述。当用户询问特定岗位的要求、类似岗位的技能需求时调用。

    Args:
        query: 搜索关键词或岗位描述，如"Java后端开发"、"产品经理"
        k: 返回结果数量，默认 5
    """
    try:
        # 1. 调用向量库检索
        results = await search_jds(query, k=k)
        # 2. 空结果直接返回提示
        if not results:
            return "未找到匹配的 JD"
        # 3. 转 JSON 字符串返回给 Agent
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.exception("search_jd 工具调用失败: query=%s", query)
        return f"JD 检索失败: {e}"
