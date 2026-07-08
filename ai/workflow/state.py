from typing import TypedDict

"""
Pipeline 状态定义：4 个节点间传递的共享状态
"""


class PipelineState(TypedDict):
    resume_text: str
    target_jd: str
    suggestions: list[dict]
    ability_profile: dict
    score_assessment: dict
    dimension_report: dict
    tier_suggestion: dict
    retrieved_jds: list[dict]
