# 模块 02 — 面试模拟测验 · 设计方案 v3

> **MVP 范围**：选择题测验（生成 + 作答 + 即时判题 + 评估报告 + Explain）  
> **暂缓**：追问逻辑、错题重练、主观题 — 等测验功能稳定后再加

---

## 一、核心交互流程

```
用户进入 ChatView（已绑定简历+分析结果）
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  右侧栏 Tab「面试测验」                                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 状态 A：无测验                                     │   │
│  │   [题目数量: 8]  [自定义要求...]  [✨ 生成测验]    │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 状态 B：有历史测验                                  │   │
│  │   测验历史列表（可点击查看）                         │   │
│  │   [+ 新建测验] 按钮                               │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 状态 C：生成中（loading spinner）                   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 状态 D：答题中                                     │   │
│  │   进度 3/8 · 题目 + 4 个选项                      │   │
│  │   选中 → 显示对错 + 选项解释 + 正确答案说明         │   │
│  │   [Explain] [上一题] [下一题]                      │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 状态 E：已完成                                     │   │
│  │   得分概览 · [查看完整报告] · [重新测试]            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**关键交互说明：**

1. **Explain 按钮**（复用现有对话体系）：
   - 点击 Explain → 自动向 ChatView 中间聊天区的输入框填入提示词
   - 提示词模板：
     ```
     I am taking a quiz on this material and was given this question: "[题目]"
     I chose this as the answer: "[用户选项]"
     That answer was [correct/incorrect]. The correct answer is "[正确答案]".
     Help me understand why my answer was [correct/incorrect].
     ```
   - 用户手动点击"发送"后，AI 在聊天区给出深入解释
   - **完全复用现有 Conversation/Message 体系，不额外写对话逻辑**

2. **选项描述（option description）**：
   - AI 生成题目时，每个选项都带 `description` 字段（说明为什么对/错）
   - 作答前只显示选项文字，作答后显示 description + 正确选项高亮 + explanation

3. **数据流**：AI 一次请求返回完整 JSON（题目 + 选项 + 答案 + 解释 + 描述）→ 存 DB → 返回前端。后续答题只做本地比对，不再调 AI。

---

## 二、数据库设计

### 2.1 `quiz_sessions` 表

```sql
CREATE TABLE quiz_sessions (
    id               BIGINT PRIMARY KEY AUTOINCREMENT,
    user_id          BIGINT NOT NULL,                          -- 用户 ID
    conversation_id  BIGINT NOT NULL,                          -- 关联的对话（对话绑定了简历）
    title            VARCHAR(100) NOT NULL,                    -- 测验标题（用户输入）
    target_jd        TEXT,                                     -- JD 上下文快照
    question_count   INT NOT NULL DEFAULT 8,                   -- 题目数量
    user_requirements TEXT,                                    -- 用户自定义要求
    status           VARCHAR(20) DEFAULT 'in_progress',        -- in_progress / completed
    score            INT,                                      -- 总分（答对数）
    report           JSON,                                     -- 评估报告
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 `quiz_questions` 表

```sql
CREATE TABLE quiz_questions (
    id               BIGINT PRIMARY KEY AUTOINCREMENT,
    session_id       BIGINT NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    stem             TEXT NOT NULL,                            -- 题目题干
    options          JSON NOT NULL,                            -- [{id, label, text, description}]
    correct_option_id VARCHAR(10) NOT NULL,                    -- 正确答案选项 ID（如 "a"）
    explanation      TEXT NOT NULL,                            -- 正确答案的详细解释
    topic_tags       JSON,                                    -- 主题标签 ["敏捷", "设计模式"]
    category         VARCHAR(20),                             -- basic / project / behavioral
    user_answer      VARCHAR(10),                             -- 用户选择的选项 ID（nullable）
    is_correct       BOOLEAN,                                 -- 用户是否答对（nullable）
    order_index      INT NOT NULL,                            -- 题目序号
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**说明：**
- 不再单独存 `reference_answer` — 选择题的正确答案就是 `correct_option_id`
- `options` 是 JSON 数组，每个选项含 `description`（AI 生成时就写好的选项解释）
- `explanation` 是正确答案的详细解析（类似 NotebookLM 选项底部的那行说明，但放在点击选项后展示）
- `topic_tags` 用于报告中的分类统计
- `user_answer` / `is_correct` 作答后更新，**不调 AI**，纯前端比对 + 后端落库

---

## 三、API 设计

```
POST   /api/quiz/create               → 创建测验 + AI 生成题目 → 返回 session + questions
POST   /api/quiz/{session_id}/answer   → 提交单题答案 → 返回 is_correct + explanation
POST   /api/quiz/{session_id}/finish   → 结束测验 → AI 生成评估报告
GET    /api/quiz/list                  → 测验历史列表（分页，按 conversation_id 过滤）
GET    /api/quiz/{session_id}          → 测验详情（含所有题目 + 报告）
DELETE /api/quiz/{session_id}          → 删除测验
```

### 3.1 `POST /api/quiz/create`

**Request:**
```json
{
    "conversation_id": 1,
    "title": "微服务面试突击测验",
    "question_count": 8,
    "user_requirements": "重点考察微服务和分布式系统相关知识点"
}
```

**处理流程：**
1. 根据 `conversation_id` 查 `Resume`，取 `target_jd`、`ability_profile`、`suggestions`
2. 构造 Prompt → 调 AI → 返回完整 JSON
3. 创建 `quiz_sessions` + 批量插入 `quiz_questions`
4. 返回 session + questions 给前端

**Response（一次性返回全部，前端本地判题）：**
```json
{
    "session": {
        "id": 1,
        "title": "软件工程测验",
        "question_count": 8,
        "status": "in_progress",
        "created_at": "..."
    },
    "questions": [
        {
            "id": 1,
            "stem": "当项目需求非常明确时，最适合采用哪种模型？",
            "options": [
                { "id": "a", "label": "A", "text": "原型模型", "description": "主要用于需求不明确时通过迭代来澄清需求" },
                { "id": "b", "label": "B", "text": "瀑布模型", "description": "在需求明确且稳定的情况下效率最高" }
            ],
            "correct_option_id": "b",
            "explanation": "瀑布模型是经典的线性顺序模型...",
            "topic_tags": ["软件生命周期"],
            "category": "basic",
            "order_index": 1
        }
    ]
}
```

> **注意**：虽然 `correct_option_id` 和 `explanation` 返回给了前端，但前端应在用户作答后才展示。前端通过 CSS 控制可见性，而非调另一个 API 获取。

### 3.2 `POST /api/quiz/{session_id}/answer`

**Request：**
```json
{
    "question_id": 1,
    "selected_option_id": "b"
}
```

**处理：** 后端更新 `quiz_questions.user_answer` + `quiz_questions.is_correct`，返回判题结果。

**Response：**
```json
{
    "is_correct": true,
    "correct_option_id": "b",
    "explanation": "瀑布模型是经典的线性顺序模型..."
}
```

> 虽然前端已经有 `correct_option_id` 和 `explanation`，但这个 API 仍然存在是因为：
> 1. 需要将用户的答案落库（持久化）
> 2. 防止前端篡改：后端权威判题，前端以 API 返回的 `is_correct` 为准

### 3.3 `POST /api/quiz/{session_id}/finish`

**Request：** 无需 body（也可以传 `{}`）

**处理：** 收集所有题目的答题结果，调 AI 生成结构化评估报告（固定 JSON 格式），更新 `quiz_sessions.status=completed` + `quiz_sessions.score` + `quiz_sessions.report`。

**Response：**
```json
{
    "total_questions": 8,
    "correct_count": 6,
    "incorrect_count": 2,
    "score_percent": 75,
    "grade": "良好",
    "categories": [
        { "name": "敏捷开发", "correct": 2, "total": 3, "percent": 67 }
    ],
    "strengths": ["软件生命周期理解到位"],
    "weaknesses": ["CI/CD 实践需要加强"],
    "suggestions": [
        { "topic": "CI/CD 与 DevOps", "tip": "阅读《持续交付》+ 用 GitHub Actions 搭建个人流水线" }
    ]
}
```

### 3.4 `GET /api/quiz/list`

**Query params:** `conversation_id`（必填，因为测验绑定对话）, `page`, `page_size`

**Response：**
```json
{
    "total": 5,
    "items": [
        { "id": 1, "title": "软件工程测验", "question_count": 8, "score": 6, "status": "completed", "created_at": "..." }
    ]
}
```

### 3.5 `GET /api/quiz/{session_id}`

返回 session + 所有 questions（含用户答案）。用于恢复进度或查看历史。

### 3.6 `DELETE /api/quiz/{session_id}`

软删或硬删 session + 级联删除 questions。

---

## 四、AI 层设计

### 4.1 Prompt 策略

一次 LLM 调用返回完整 JSON（题目 + 选项 + 答案 + 解释 + 描述），**不反复调 AI**。

**System Prompt 核心要点：**
```
你是严格的面试出题官。根据以下内容生成 {question_count} 道单选题：

1. 岗位 JD：{target_jd}
2. 候选人能力画像：{ability_profile}
3. 简历优化建议：{suggestions}
4. 用户额外要求：{user_requirements}

要求：
- 输出纯 JSON（不要 markdown 包裹）
- 每道题 4 个选项（A/B/C/D）
- 每个选项都有 description 字段（一行简短说明该项为什么对/错）
- 正确答案有 explanation 字段（50-150 字详细解析）
- 题目覆盖三类：基础题 40%、项目题 30%、行为题 30%
- 每道题附带 topic_tags 数组
```

### 4.2 Pydantic Schema（`schemas/quiz.py`）

```python
class QuizOption(BaseModel):
    id: str          # "a", "b", "c", "d"
    label: str       # "A", "B", "C", "D"
    text: str        # 选项文字
    description: str # 选项解释（为什么对/错）

class QuizQuestion(BaseModel):
    stem: str
    options: list[QuizOption]
    correct_option_id: str
    explanation: str
    topic_tags: list[str]
    category: str    # basic / project / behavioral

class QuizGenerateOutput(BaseModel):
    questions: list[QuizQuestion]

class QuizReportOutput(BaseModel):
    total_questions: int
    correct_count: int
    incorrect_count: int
    score_percent: int
    grade: str                         # "优秀" / "良好" / "一般" / "需要加强"
    categories: list[CategoryScore]    # 按 topic_tags 聚合得分
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[SuggestionItem]  # 针对性学习建议
```

### 4.3 出题 Chain（`ai/chains/quiz.py`）

这个模块**不需要**复杂的 StateGraph（没有追问循环），只需要一个简单的异步函数：

```python
async def generate_quiz(
    target_jd: str,
    ability_profile: dict,
    suggestions: list[dict],
    question_count: int,
    user_requirements: str,
) -> QuizGenerateOutput:
    # 1. 构造 prompt → 2. 调 LLM → 3. extract_json() → 4. model_validate()
```

### 4.4 报告生成 Chain（`ai/chains/quiz_report.py`）

`/finish` 时调 AI 生成报告，返回固定 JSON 格式，前端渲染。同样是一次 LLM 调用：

```python
async def generate_report(
    questions: list[dict],       # 所有题目 + 用户答案 + 对错
    ability_profile: dict,
) -> QuizReportOutput:
    # 输入：答题结果 + 能力画像 → 输出：结构化评估报告 JSON
```

---

## 五、前端设计（集成到现有 ChatView）

### 5.1 右侧栏改造

现有右侧栏是"优化建议"翻页面板。改造为 **双标签切换**：

```
┌─────────────────────────┐
│ [优化建议]  [面试测验]   │  ← 两个 Tab
├─────────────────────────┤
│                         │
│   Tab 内容区             │
│                         │
└─────────────────────────┘
```

### 5.2 Tab「面试测验」的 5 个状态

#### 状态 1：无测验 / 点击「+ 新建测验」

用户点击「+ 新建测验」或初始无测验时，显示生成表单：

```
┌──────────────────────────┐
│  🎯 新建面试测验          │
│                          │
│  测验标题                 │
│  ┌────────────────────┐  │
│  │ 微服务面试突击测验    │  │
│  └────────────────────┘  │
│                          │
│  题目数量: [8]  ▼        │
│  (可选 5 / 8 / 10 / 15)  │
│                          │
│  自定义要求（可选）        │
│  ┌────────────────────┐  │
│  │ 重点考察微服务和分布  │  │
│  │ 式系统相关知识点...   │  │
│  └────────────────────┘  │
│                          │
│  [✨ 生成测验题目]        │
│  [取消]                  │
└──────────────────────────┘
```

#### 状态 2：有历史测验
```
┌──────────────────────────┐
│  [+ 新建测验]             │
│  ─────────────────────── │
│  测验历史                 │
│  ┌────────────────────┐  │
│  │ 软件工程测验         │  │
│  │ 8 题 · 6/8 · 良好   │  │
│  │ 2024-07-05          │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │ Java 基础测验        │  │
│  │ 10 题 · 8/10 · 优秀  │  │
│  │ 2024-07-03          │  │
│  └────────────────────┘  │
└──────────────────────────┘
```

#### 状态 3：生成中（Loading）
```
┌──────────────────────────┐
│                          │
│       ◠ ◠ ◠             │
│    正在生成测验题目…      │
│    AI 正在分析 JD 并      │
│    定制化出题...          │
│                          │
└──────────────────────────┘
```

#### 状态 4：答题中
```
┌──────────────────────────┐
│  📝 软件工程测验   3/8    │
│  ─────────────────────── │
│  3. Scrum 框架中，Sprint │
│  的推荐时长通常是？       │
│                          │
│  ┌────────────────────┐  │
│  │ ○ A  1 天           │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │ ● B  1 到 4 周  ✓  │  │  ← 选中后显示对错
│  │   这是正确的时长范围  │  │  ← 显示 option.description
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │ ○ C  3 个月         │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │ ○ D  6 个月         │  │
│  └────────────────────┘  │
│                          │
│  💡 Scrum Guide 明确规定 │  ← explanation
│  Sprint 不超过一个月...   │
│                          │
│  [? Explain] [← 上一题]  │
│              [下一题 →]  │
└──────────────────────────┘
```

#### 状态 5：已完成（迷你报告）
```
┌──────────────────────────┐
│  📊 测验报告              │
│                          │
│       ● 6/8              │
│       75% 良好            │
│                          │
│  正确: 6  错误: 2         │
│                          │
│  [查看完整报告]            │
│  [重新测验]               │
│  [Review 错题]            │
└──────────────────────────┘
```

### 5.3 Explain 按钮交互

点击 Explain → 填充聊天区输入框（不自动发送），Prompt 模板：

```
I am taking a quiz on this material and was given this question: "Scrum 框架中，Sprint 的推荐时长通常是多久？"

I chose this as the answer: "1 天"

That answer was incorrect. The correct answer is "1 到 4 周"

Help me understand why my answer was incorrect and learn more about Scrum Sprint best practices.
```

用户点击"发送"后，走现有的 `sendMessage` → AI 在聊天区用 Markdown 给出深入解释。

### 5.4 完整报告（右侧栏内，压缩尺寸）

点击"查看完整报告"后，在右侧栏内展开完整报告视图（可滚动），**不开新页面、不做全屏弹窗**。报告由 AI 生成固定 JSON 格式，前端渲染。

由于空间有限（~400px 宽），报告采用压缩样式：环形图缩小、字体紧凑、卡片间距收窄。参考前端原型 `index.html` 的 result page 结构：

1. **总分环形图**（~100px）+ 正确/错误统计
2. **分类得分条形图**（紧凑版）
3. **强项 / 薄弱项**（双列布局，字体缩小）
4. **针对性学习建议**（单列卡片）
5. **Review Quiz**（逐题回顾）/ **Retake Quiz** 按钮

### 5.5 布局调整

为容纳测验面板的完整报告，ChatView 三栏宽度需调整：

| 栏 | 当前宽度 | 调整后 |
|----|---------|--------|
| 左侧栏（分析报告） | 340px | **380px** |
| 中间栏（聊天区） | flex:1 | **flex:1**（自动撑满剩余空间） |
| 右侧栏（建议+测验） | 360px | **380px**（与左侧等宽） |

**约束：中间 > 两侧，两侧等宽，中间与两侧保留间距（`gap`）。**

以 1440px 视口为例：`(1440 - 380×2 - gap×2) ≈ 640px` 留白给中间聊天区，满足 640 > 380。

实际实现通过 CSS：
```css
.chat-view {
  display: flex;
  gap: 0;              /* 面板之间用 border 分隔，不加额外 gap */
}
.analysis-panel  { width: 380px; flex-shrink: 0; }
.chat-area       { flex: 1; min-width: 480px; }
.result-panel    { width: 380px; flex-shrink: 0; }
```

响应式：≤1100px 隐藏左侧栏，≤920px 隐藏右侧栏（与现有逻辑一致）。

### 5.6 Tab 切换时的状态保留

右侧栏有两张 Tab：「优化建议」和「面试测验」。用户在测验做到一半（如第 3 题）时切到「优化建议」再切回来：

- **测验进度应保留**：Vue 中用 `v-show` 而非 `v-if` 切换 Tab 内容，组件不销毁，状态不丢失
- 同理，从测验 tab 切到建议 tab 时，建议的翻页位置也保留

> 简单说：两个 Tab 的面板始终存活在 DOM 中，只是 `display: none/block` 切换，切换时状态完全不丢失。

---

## 六、与现有代码的复用

| 现有模块 | 复用方式 |
|----------|----------|
| `ai/model/deepseek.py` | 复用 `get_resume_llm()` 低温度出题 |
| `ai/chains/utils.py` | 复用 `extract_json()` |
| `core/database.py` | 复用 `get_db` 依赖注入 |
| `schemas/response.py` | 复用 `ApiResponse` |
| `middleware/auth.py` | 复用 `get_current_user_id` |
| `api/conversation.py` | 路由 + 鉴权模式参考 |
| `services/conversation.py` | list/get/delete 模式参考 |
| `frontend/src/api/request.js` | 复用 axios 实例 |
| `ChatView.vue` | 复用聊天消息渲染 + Markdown + AI typing |
| `Resume.target_jd` / `ability_profile` | 直接读取作为出题上下文 |
| **Explain → 对话区** | 完全复用现有 Message 体系，不额外实现 |

---

## 七、前端组件拆分

```
frontend/src/
├── api/
│   └── quiz.js                    # 新增：测验 API 调用
├── components/
│   └── QuizPanel.vue              # 新增：右侧栏测验面板（核心组件）
│       ├── QuizGenerateForm.vue   #   子：生成测验表单
│       ├── QuizHistoryList.vue    #   子：历史测验列表
│       ├── QuizQuestion.vue       #   子：单题展示 + 选项
│       ├── QuizReport.vue         #   子：迷你报告 / 完整报告
│       └── QuizLoading.vue        #   子：生成中 loading
├── views/
│   └── ChatView.vue               # 修改：右侧栏增加 Tab 切换
```

---

## 八、执行路径（5 个里程碑）

每个里程碑完成后我会汇报：做了什么、改了哪些文件、为什么这么改、怎么测试、下一步是什么。

---

### 里程碑 1：数据库 + 数据模型

**目标**：两张新表能在 MySQL 中建好，SQLAlchemy 模型能正常映射。

**我要做的事：**
1. 在 `resource/init.sql` 末尾追加 `quiz_sessions` 和 `quiz_questions` 的 DDL
2. 新建 `models/quiz.py`，写两个 SQLAlchemy 模型
3. 新建 `schemas/quiz.py`，写所有 Pydantic 请求/响应/AI 输出模型

**涉及文件：**
- `resource/init.sql` — 追加两段 `CREATE TABLE`
- `models/quiz.py` — 新增，`QuizSession` + `QuizQuestion` 模型
- `schemas/quiz.py` — 新增，请求/响应/AI 输出全部 Pydantic schema

**你要做的事：**
- 把 init.sql 里新增的 DDL 拿到 MySQL Workbench 里执行建表
- 启动 FastAPI 确认没有 import 报错

---

### 里程碑 2：AI 层（Prompt + Chain）

**目标**：能调 AI 出题和生成报告，返回合法 JSON。

**我要做的事：**
1. 新建 `ai/prompts/quiz.py` — 出题 System Prompt + 用户 Prompt 构建函数
2. 新建 `ai/chains/quiz.py` — `generate_quiz()` 异步函数
3. 新建 `ai/chains/quiz_report.py` — `generate_report()` 异步函数

**设计要点：**
- Prompt 拼接顺序：System Prompt（角色 + JSON 格式约束）→ 用户上下文（JD + 能力画像 + 简历建议 + 用户自定义要求）
- 用户自定义要求通过 `build_user_prompt()` 拼接到 prompt 中发给 AI
- 两道独立的 Chain，都是 `extract_json()` 手动解析（DeepSeek 不支持 structured output）

**涉及文件：**
- `ai/prompts/quiz.py` — 新增
- `ai/chains/quiz.py` — 新增
- `ai/chains/quiz_report.py` — 新增

**你要做的事：**
- 启动 FastAPI，不需要专门的测试端点（下一里程碑才有），我可以在 milestone 2 结尾写一个简单的手动测试脚本来验证 AI 调用能正常返回 JSON

---

### 里程碑 3：Service + API 路由

**目标**：6 个 API 端点全部可用，Swagger 可测试。

**我要做的事：**
1. 新建 `services/quiz.py` — 所有业务逻辑
2. 新建 `api/quiz.py` — 6 个路由端点
3. 修改 `main.py` — 注册 quiz router

**6 个端点：**
- `POST /api/quiz/create` — 核心：查 Resume 上下文 → 调 AI 出题 → 写 DB → 返回
- `POST /api/quiz/{id}/answer` — 保存答案 + 判题（后端权威判题）
- `POST /api/quiz/{id}/finish` — 调 AI 生成报告 → 更新 session
- `GET /api/quiz/list?conversation_id=1` — 测验历史
- `GET /api/quiz/{id}` — 测验详情
- `DELETE /api/quiz/{id}` — 删除测验 + 级联删题

**涉及文件：**
- `services/quiz.py` — 新增
- `api/quiz.py` — 新增
- `main.py` — 修改（加一行 `include_router`）

**你要做的事：**
- 打开 `http://127.0.0.1:8000/docs` Swagger
- 先调 `POST /api/quiz/create`，传入 `conversation_id`、`title`、`question_count`、`user_requirements`
- 检查返回的 JSON 是否包含 session + questions（questions 里有 options、correct_option_id、explanation 等字段）
- 再依次测试 answer、finish、list、detail、delete

---

### 里程碑 4：前端 API 层 + QuizPanel 核心组件

**目标**：右侧栏能生成测验、答题、查看报告。

**我要做的事：**
1. 新建 `frontend/src/api/quiz.js` — 封装 6 个 API 调用
2. 新建 `frontend/src/components/QuizPanel.vue` — 核心容器（5 状态切换）
3. 新建 `QuizGenerateForm.vue`、`QuizHistoryList.vue`、`QuizQuestion.vue`、`QuizReport.vue`、`QuizLoading.vue` 子组件
4. 修改 `ChatView.vue` — 右侧栏加「优化建议 / 面试测验」双标签 + 宽度调整 340→380 / 360→380

**5 个状态流转：**
```
[表单] → (提交) → [Loading] → (AI返回) → [答题中] → (做完/手动结束) → [报告]
                                                        ↓
                                                  [历史列表] ← (返回)
```

**涉及文件：**
- `frontend/src/api/quiz.js` — 新增
- `frontend/src/components/QuizPanel.vue` — 新增
- `frontend/src/components/QuizGenerateForm.vue` — 新增
- `frontend/src/components/QuizHistoryList.vue` — 新增
- `frontend/src/components/QuizQuestion.vue` — 新增
- `frontend/src/components/QuizReport.vue` — 新增
- `frontend/src/components/QuizLoading.vue` — 新增
- `frontend/src/views/ChatView.vue` — 修改

**你要做的事：**
- 前端 `npm run dev` 启动
- 在上传简历并分析完成后，进入 ChatView
- 右侧栏切换到「面试测验」tab，填写表单点生成
- 观察 loading → 题目出现 → 逐题选择 → 看对错反馈 → 完成看报告

---

### 里程碑 5：Explain 功能 + 收尾

**目标**：Explain 按钮联调通过，全流程跑通。

**我要做的事：**
1. 在 `QuizQuestion.vue` 中给每个选项加 Explain 按钮
2. 点击 Explain → 将题目+答案拼成 Prompt → 填入聊天区输入框
3. 用户手动发送 → 走现有 `sendMessage` → AI 在聊天区解释

**不需要**新建对话或额外 API — 完全复用现有 Conversation/Message 体系。

**涉及文件：**
- `frontend/src/components/QuizQuestion.vue` — 修改（加 Explain 按钮 + emit 事件）
- `frontend/src/components/QuizPanel.vue` — 修改（接收事件 → 传给 ChatView）
- `frontend/src/views/ChatView.vue` — 修改（接收填充输入框事件）

**你要做的事：**
- 在做完一道题后（不管对错），点击选项旁边的 "Explain" 按钮
- 观察聊天区输入框是否自动填充了 Prompt
- 手动点击发送，看 AI 是否给出了正确的解释
- 端到端：创建测验 → 答完 8 题 → 看报告 → 对某题点 Explain → 聊天区解释

---

### 里程碑完成后总结

| 里程碑 | 后端新增 | 后端修改 | 前端新增 | 前端修改 |
|--------|---------|---------|---------|---------|
| M1 SQL+Model | 3 文件 | 1 文件 | 0 | 0 |
| M2 AI Chain | 3 文件 | 0 | 0 | 0 |
| M3 API | 2 文件 | 1 文件 | 0 | 0 |
| M4 前端核心 | 0 | 0 | 7 文件 | 1 文件 |
| M5 Explain | 0 | 0 | 0 | 3 文件 |
| **合计** | **8 新** | **2 改** | **7 新** | **4 改** |
