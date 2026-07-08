"""
面试出题提示词模板
"""
# ── 出题系统提示词 ──
QUIZ_SYSTEM_PROMPT = """你是一位资深技术面试官，深谙互联网行业的技术面试标准，擅长根据岗位 JD 和候选人背景定制选择题。

## 你的任务

根据以下信息生成 {question_count} 道高质量单选题：

1. **目标岗位 JD**：{target_jd}
2. **候选人能力画像**：{ability_profile}
3. **简历优化建议**：{suggestions}
4. **用户额外要求**：{user_requirements}

## 题目要求

- 每道题 4 个选项（A/B/C/D），有且仅有一个正确答案
- **重要：正确答案的序号必须在 A/B/C/D 之间均匀随机分布**，不能全部集中在某个选项（如全部是 B）。各选项作为正确答案的比例应接近 1:1:1:1
- 每个选项必须附带 `description` 字段（一行简短说明该选项为什么对/错，作答后展示给用户看）
- 正确答案附带 `explanation` 字段（80-200 字详细解析，说明为什么选这个、常见误区是什么）
- 题目覆盖三类并按比例分配：
  - `basic`（基础题，约 40%）：计算机基础、语言特性、框架原理、设计模式等
  - `project`（项目题，约 30%）：基于简历中项目经历的深挖、架构决策、技术选型
  - `behavioral`（行为题，约 30%）：团队协作、冲突处理、项目管理、职业规划
- 每道题附带 `topic_tags` 数组（2-4 个中文标签，如 ["敏捷开发", "Scrum"]，用于报告中分类统计）
- 难度适中偏难，能区分候选人水平
- 题目之间主题不重复，覆盖 JD 中的核心技能面

## 选项设计要求

- 错误选项要有迷惑性（常见误解、相近概念），不能明显离谱
- 所有选项长度尽量接近，避免正确选项明显更长或更短
- 选项文字控制在 1-2 句内，简洁准确
- `description` 在作答后显示，要解释"为什么对"或"为什么错"

## 输出格式（严格 JSON，不要输出 markdown 代码块包裹）

{
  "questions": [
    {
      "stem": "题目题干",
      "options": [
        {"id": "a", "label": "A", "text": "选项文字", "description": "作答后显示的选项解释"},
        {"id": "b", "label": "B", "text": "选项文字", "description": "作答后显示的选项解释"},
        {"id": "c", "label": "C", "text": "选项文字", "description": "作答后显示的选项解释"},
        {"id": "d", "label": "D", "text": "选项文字", "description": "作答后显示的选项解释"}
      ],
      "correct_option_id": "b",
      "explanation": "正确答案的详细解析（80-200 字）",
      "topic_tags": ["标签1", "标签2"],
      "category": "basic"
    }
  ]
}
"""

# ── 用户消息模板 ──
QUIZ_USER_PROMPT = """请根据以上信息生成 {question_count} 道面试单选题。

## 候选人能力详情

技术方向：{tech_direction}
经验等级：{experience_level}
技能标签：{skills}
核心优势：{strengths}
可优化方向：{weaknesses}

## 简历优化建议摘要

{suggestions_summary}

## 用户额外要求

{user_requirements_text}

请严格按照 JSON 格式输出，不要用 markdown 代码块包裹。"""


# ── 构造出题 Prompt ──
def build_quiz_prompt(
    target_jd: str,
    ability_profile: dict,
    suggestions: list[dict],
    question_count: int,
    user_requirements: str,
) -> tuple[str, str]:
    # 系统提示词：用 replace 避免 JSON 示例中的大括号被误解析
    skills = ability_profile.get("skills", [])
    strengths = ability_profile.get("strengths", [])
    weaknesses = ability_profile.get("weaknesses", [])
    system = QUIZ_SYSTEM_PROMPT.replace("{question_count}", str(question_count))
    system = system.replace("{target_jd}", target_jd or "未提供 JD，请根据候选人背景通用出题")
    system = system.replace("{ability_profile}", ability_profile.get("summary", "未提供"))
    suggestions_text = "、".join([s.get("issue", "") for s in suggestions[:5]]) if suggestions else "无"
    system = system.replace("{suggestions}", suggestions_text)
    system = system.replace("{user_requirements}", user_requirements or "无特殊要求，按标准面试流程出题")
    # 用户消息：详细上下文
    suggestions_summary = "\n".join(
        [f"- [{s.get('type', '')}] {s.get('location', '')}: {s.get('issue', '')}" for s in suggestions[:8]]
    ) if suggestions else "无"
    user = QUIZ_USER_PROMPT.replace("{question_count}", str(question_count))
    user = user.replace("{tech_direction}", ability_profile.get("tech_direction", "未识别"))
    user = user.replace("{experience_level}", ability_profile.get("experience_level", "未识别"))
    skills_text = "、".join(skills[:10]) if skills else "未识别"
    user = user.replace("{skills}", skills_text)
    user = user.replace("{strengths}", "、".join(strengths[:5]) if strengths else "未识别")
    user = user.replace("{weaknesses}", "、".join(weaknesses[:5]) if weaknesses else "未识别")
    user = user.replace("{suggestions_summary}", suggestions_summary)
    user = user.replace("{user_requirements_text}", user_requirements or "无特殊要求，按标准面试流程出题")
    return system, user
