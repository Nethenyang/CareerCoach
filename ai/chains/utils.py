import json

"""
公共工具：从 LLM 回复中提取 JSON
DeepSeek 不支持 with_structured_output，需手动解析 JSON 响应。
"""

def extract_json(content: str) -> dict:
    """从 LLM 回复中提取 JSON，处理 markdown 代码块包裹的情况"""
    content = content.strip()
    # 情况1：```json ... ```
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0]
    # 情况2：``` ... ```
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0]
    content = content.strip()
    return json.loads(content)
