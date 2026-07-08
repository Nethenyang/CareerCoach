import json
import logging
from langchain_core.tools import tool
from ai.config import ai_settings

"""
Web 搜索工具：Agent 可调用，基于 Tavily API
"""
logger = logging.getLogger(__name__)


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """搜索互联网获取外部信息。当用户询问行业趋势、薪资水平、公司招聘动态等需要实时信息的问题时调用。

    Args:
        query: 搜索查询词
        max_results: 最大返回结果数，默认 5
    """
    try:
        # 1. 构建 Tavily 客户端
        from tavily import AsyncTavilyClient
        client = AsyncTavilyClient(api_key=ai_settings.TAVILY_API_KEY)
        # 2. 异步搜索
        response = await client.search(query, max_results=max_results)
        # 3. 提取结果转成统一格式
        results = []
        for item in response.get("results", []):
            result_item = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
            results.append(result_item)
        # 4. 转 JSON 字符串返回给 Agent
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.exception("web_search 工具调用失败: query=%s", query)
        return f"Web 搜索失败: {e}"
