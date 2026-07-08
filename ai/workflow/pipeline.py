import json
import logging
import asyncio
from langgraph.graph import StateGraph, END
from ai.workflow.state import PipelineState
from ai.chains.resume import analyze_resume
from ai.chains.ability import evaluate_ability
from ai.chains.score import evaluate_score
from ai.chains.dimension import evaluate_dimensions, evaluate_strategic_suggestions
from ai.chains.tier import suggest_tier
from ai.vectorstore.jd_store import search_jds
from ai.config import ai_settings

logger = logging.getLogger(__name__)

"""
6 节点固定管道：analyze → evaluate → score → dimension → suggest_tier → retrieve_jds → END
"""


# ── Node 1: 简历分析 ──
async def analyze_node(state: PipelineState) -> dict:
    # 1. 取出输入文本
    resume_text = state["resume_text"]
    target_jd = state.get("target_jd", "")
    # 2. 异步调用简历分析链
    analysis_result = await analyze_resume(resume_text, target_jd)
    # 3. 把 Pydantic 对象逐个转字典
    suggestions_list = []
    for s in analysis_result.suggestions:
        dict_item = s.model_dump()
        suggestions_list.append(dict_item)
    # 4. 返回字典更新 state
    return {"suggestions": suggestions_list}


# ── Node 2: 能力评估 ──
async def evaluate_node(state: PipelineState) -> dict:
    # 1. 取出简历文本和上一步的建议
    resume_text = state["resume_text"]
    suggestions = state["suggestions"]
    # 2. 异步调用能力评估链
    profile = await evaluate_ability(resume_text, suggestions)
    # 3. Pydantic 对象转字典
    profile_dict = profile.model_dump()
    # 4. 返回字典更新 state
    return {"ability_profile": profile_dict}


# ── Node 3: 评分报告 ──
async def score_node(state: PipelineState) -> dict:
    # 1. 取出简历文本和上一步的能力画像
    resume_text = state["resume_text"]
    ability_profile = state["ability_profile"]
    # 2. 异步调用评分链
    score_data = await evaluate_score(resume_text, ability_profile)
    # 3. 返回字典更新 state
    return {"score_assessment": score_data}


# ── Node 4: 维度分析（4维度+战略建议，并行调用） ──
async def dimension_node(state: PipelineState) -> dict:
    # 1. 取出简历文本和能力画像
    resume_text = state["resume_text"]
    ability_profile = state["ability_profile"]
    # 2. 并行调用两个 chain
    dimensions_result, suggestions_result = await asyncio.gather(
        evaluate_dimensions(resume_text),
        evaluate_strategic_suggestions(resume_text, ability_profile),
    )
    # 3. 合并结果
    report = {
        "dimensions": dimensions_result["dimensions"],
        "strategic_suggestions": suggestions_result["strategic_suggestions"],
    }
    # 4. 返回字典更新 state
    return {"dimension_report": report}


# ── Node 5: 梯队建议 ──
async def suggest_tier_node(state: PipelineState) -> dict:
    # 1. 取出上一步的能力画像
    ability_profile = state["ability_profile"]
    # 2. 异步调用梯队建议链
    suggestion = await suggest_tier(ability_profile)
    # 3. Pydantic 对象转字典
    suggestion_dict = suggestion.model_dump()
    # 4. 返回字典更新 state
    return {"tier_suggestion": suggestion_dict}


# ── web search 兜底：向量库不足 3 条时调用 Tavily 补充 ──
async def _web_search_jds(tech_direction: str, tier: str) -> list[dict]:
    try:
        # 1. 构建 Tavily 客户端
        from tavily import AsyncTavilyClient
        client = AsyncTavilyClient(api_key=ai_settings.TAVILY_API_KEY)
        # 2. 拼接搜索 query
        query = f"{tech_direction}工程师 招聘要求 {tier}"
        # 3. 异步搜索
        response = await client.search(query, max_results=5)
        # 4. 把 Tavily 结果转成和向量库一致的格式
        results = []
        for item in response.get("results", []):
            jd_item = {
                "jd_id": 0,
                "score": 0.0,
                "company": "",
                "position": f"{tech_direction}工程师",
                "tier": tier,
                "tech_direction": tech_direction,
                "requirements": item.get("content", ""),
                "source_url": item.get("url", ""),
            }
            results.append(jd_item)
        return results
    except Exception:
        logger.exception("web_search 兜底失败: tech_direction=%s tier=%s", tech_direction, tier)
        return []


# ── Node 6: JD 检索（向量库 + web 兜底） ──
async def retrieve_jds_node(state: PipelineState) -> dict:
    # 1. 从 state 取出梯队和技术方向
    tier = state["tier_suggestion"]["tier"]
    skills = state["ability_profile"]["skills"]
    tech_direction = state["ability_profile"]["tech_direction"]
    # 2. 用前 5 个技能拼检索 query
    query = " ".join(skills[:5])
    # 3. 向量库语义检索（按 tier 过滤）
    jds = await search_jds(query, tiers=[tier], k=5)
    # 4. 不足 3 条走 web search 兜底
    if len(jds) < 3:
        logger.info("向量库仅 %d 条 JD，触发 web search 兜底", len(jds))
        web_jds = await _web_search_jds(tech_direction, tier)
        jds.extend(web_jds)
    # 5. 返回字典更新 state
    return {"retrieved_jds": jds}


# ── 组装 StateGraph ──
graph = StateGraph(PipelineState)
graph.add_node("analyze", analyze_node)
graph.add_node("evaluate", evaluate_node)
graph.add_node("score", score_node)
graph.add_node("dimension", dimension_node)
graph.add_node("suggest_tier", suggest_tier_node)
graph.add_node("retrieve_jds", retrieve_jds_node)
graph.add_edge("analyze", "evaluate")
graph.add_edge("evaluate", "score")
graph.add_edge("evaluate", "dimension")
graph.add_edge("evaluate", "suggest_tier")
graph.add_edge("score", "retrieve_jds")
graph.add_edge("dimension", "retrieve_jds")
graph.add_edge("suggest_tier", "retrieve_jds")
graph.add_edge("retrieve_jds", END)
graph.set_entry_point("analyze")
compiled_graph = graph.compile()


def get_pipeline():
    return compiled_graph
