# Career Coach

AI 智能简历分析与面试教练平台 —— 上传 PDF 简历，获得深度分析报告、AI 职业对话、定制化面试测验。

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | FastAPI（异步） + Uvicorn |
| AI 框架 | LangChain + LangGraph（StateGraph 管道 + ReAct Agent） |
| 大语言模型 | DeepSeek |
| Embedding | DashScope（阿里云） |
| 关系数据库 | MySQL 8.0 + SQLAlchemy 2.0（async） |
| 向量数据库 | Redis Stack（RediSearch） |
| 文件存储 | 阿里云 OSS |
| 数据校验 | Pydantic ≥2.0 |
| 前端框架 | Vue 3（Composition API）+ Vite |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia |
| 包管理 | uv |

## 项目结构

```
career-coach/
├── main.py                      # FastAPI 应用入口，注册 5 个路由模块
├── pyproject.toml               # 项目配置与依赖声明
├── langgraph.json               # LangGraph Server 配置
├── .env                         # 环境变量（不入库）
│
├── api/                         # API 路由层（25 个端点）
│   ├── auth.py                  # 认证：注册、登录
│   ├── resume.py                # 简历：上传、分析、查询
│   ├── conversation.py          # 对话：创建、消息（含 SSE 流式）、列表、重命名、删除
│   ├── quiz.py                  # 测验：创建、作答、结束、列表、详情、删除、重置
│   └── knowledge.py             # JD 知识库：录入、批量导入、列表、详情、删除
│
├── services/                    # 业务逻辑层
│   ├── user.py                  # 用户：注册、登录、查询
│   ├── resume.py                # 简历：上传、PDF 解析、分析管道触发、查询、删除
│   ├── conversation.py          # 对话：创建（幂等）、列表、重命名、删除
│   ├── message.py               # 消息：发送、SSE 流式发送、历史查询、滑动窗口
│   ├── quiz.py                  # 测验：创建+AI 出题、作答判题、结束+AI 报告、重置、CRUD
│   └── knowledge.py             # JD 知识库：CRUD + Redis Stack 向量同步
│
├── schemas/                     # Pydantic 数据校验（30+ 模型）
│   ├── response.py              # 统一响应 ApiResponse
│   ├── user.py                  # 注册/登录请求、用户响应
│   ├── resume.py                # 分析请求、建议/能力/评分/维度/梯队等响应模型
│   ├── conversation.py          # 对话创建/消息/重命名请求、对话/消息响应
│   ├── quiz.py                  # 测验请求/响应 + AI 输出的 JSON Schema
│   ├── jd.py                    # JD 录入/导入请求、响应模型
│   └── chat.py                  # 聊天请求（预留）
│
├── models/                      # SQLAlchemy ORM（7 张表）
│   ├── user.py                  # User
│   ├── resume.py                # Resume（含 6 个 JSON 列）
│   ├── conversation.py          # Conversation
│   ├── message.py               # Message
│   ├── jd.py                    # JdKnowledge
│   └── quiz.py                  # QuizSession + QuizQuestion
│
├── ai/                          # AI 层
│   ├── config/settings.py       # AI 模型配置（DeepSeek、DashScope、Tavily）
│   ├── model/deepseek.py        # LLM 工厂函数（简历分析 / 通用 / 自定义温度）
│   ├── embeddings/embeddings.py # DashScope Embedding 工厂
│   ├── chains/                  # AI Chain（单一 LLM 调用）
│   │   ├── utils.py             # extract_json() — LLM 输出 → JSON 解析
│   │   ├── resume.py            # 简历分析（4 维度问题检测）
│   │   ├── ability.py           # 能力画像评估
│   │   ├── score.py             # 多维度量化评分
│   │   ├── dimension.py         # 4 维度文档质量 + 3 方向战略建议（并行）
│   │   ├── tier.py              # 求职梯队推荐
│   │   ├── quiz.py              # 面试题生成
│   │   └── quiz_report.py       # 测验评估报告生成
│   ├── workflow/                # LangGraph 编排
│   │   ├── state.py             # PipelineState（TypedDict）
│   │   └── pipeline.py          # 6 节点 StateGraph（3 路并行 + JD 检索 + Tavily 兜底）
│   ├── agents/career_coach.py   # ReAct Agent（对话教练）
│   ├── tools/                   # Agent 工具
│   │   ├── jd_tools.py          # JD 知识库语义检索
│   │   ├── search_tools.py      # Tavily 互联网搜索
│   │   └── resume_tools.py      # 简历分析结果查询
│   ├── prompts/                 # 提示词模板（8 个）
│   │   ├── chat.py              # Agent 系统提示词
│   │   ├── resume.py            # 简历分析
│   │   ├── ability.py           # 能力评估
│   │   ├── score.py             # 量化评分
│   │   ├── dimension.py         # 维度分析 + 战略建议
│   │   ├── tier.py              # 梯队建议
│   │   ├── quiz.py              # 出题
│   │   └── quiz_report.py       # 报告生成
│   └── vectorstore/jd_store.py  # Redis Stack 向量库（索引/添加/检索/删除）
│
├── core/                        # 基础设施
│   ├── config.py                # 全局配置（DB / Redis / OSS）
│   ├── database.py              # 异步引擎 + 连接池 + 会话依赖注入
│   └── security.py              # bcrypt 密码哈希与验证
│
├── middleware/auth.py           # X-User-Id 鉴权依赖
├── util/oss_client.py           # 阿里云 OSS 客户端（上传/下载/删除/预签名 URL）
├── resource/                    # 资源文件
│   ├── init.sql                 # 数据库建表脚本（7 张表 + 索引）
│   └── jd_data.json             # JD 示例数据
│
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── main.js              # 应用入口（挂载 Pinia / Router / Element Plus）
│   │   ├── App.vue              # 根组件
│   │   ├── router/index.js      # 路由 + 导航守卫
│   │   ├── stores/user.js       # Pinia 用户状态
│   │   ├── api/                 # API 调用层
│   │   │   ├── request.js       # Axios 实例 + 拦截器（X-User-Id / 响应解包）
│   │   │   ├── auth.js          # 认证 API
│   │   │   ├── resume.js        # 简历 API
│   │   │   ├── conversation.js  # 对话 API + SSE 流式消费（ReadableStream）
│   │   │   └── quiz.js          # 测验 API
│   │   ├── views/               # 页面
│   │   │   ├── LandingView.vue  # 落地页（粒子背景 + 逐字动画标题）
│   │   │   ├── LoginView.vue    # 登录/注册
│   │   │   ├── ResumeView.vue   # 简历上传与分析
│   │   │   └── ChatView.vue     # AI 对话（三栏布局 + SSE + 测验面板）
│   │   ├── layouts/AppLayout.vue # 应用壳子（步骤导航 + 对话切换）
│   │   └── components/          # 可复用组件（10 个）
│   │       ├── ParticleBg.vue        # 粒子背景
│   │       ├── ScoreGauge.vue        # SVG 环形评分图
│   │       ├── SkillBars.vue         # 技能维度条形图
│   │       ├── DimensionReport.vue   # 4 维度分析报告
│   │       ├── QuizPanel.vue         # 测验面板（5 状态容器）
│   │       ├── QuizGenerateForm.vue  # 测验生成表单
│   │       ├── QuizHistoryList.vue   # 测验历史列表
│   │       ├── QuizQuestion.vue      # 单题作答
│   │       ├── QuizReport.vue        # 测验评估报告
│   │       └── QuizLoading.vue       # 加载动画
│   ├── vite.config.js           # Vite 配置（代理 /api → 后端）
│   └── package.json
│
├── DESIGN.md                    # 测验模块设计方案
├── 设计文档.md                   # 系统设计文档
├── 功能逻辑详情.md                # 功能逻辑详细说明
├── RULES.md                     # 代码规范
└── LICENSE
```

## 核心功能

### 1. 智能简历分析

上传 PDF 简历 → 6 阶段 LangGraph 管道分析，产出：

- **优化建议**：弱动词替换、量化指标补充、结构问题、JD 差距分析
- **能力画像**：技术方向、经验等级、核心技能、优势与不足
- **量化评分**：综合评分 + 5-8 个技能维度评分
- **维度分析**：4 维度 × 子项（语言表达、信息完整性、内容相关性、简历专业性）
- **梯队推荐**：startup / mid / big_edge / big_core + 推荐理由
- **JD 匹配**：Redis Stack 向量检索 + Tavily Web Search 兜底

### 2. AI 职业教练对话

- ReAct Agent（Thinking + Tool Calling 循环）
- 工具：JD 知识库语义检索 + Tavily 互联网搜索
- SSE 流式逐字输出，支持 Markdown 渲染
- 滑动窗口对话历史管理（最近 20 条）

### 3. 面试模拟测验

- AI 根据能力画像生成定制化选择题（基础 40% / 项目 30% / 行为 30%）
- 题目数 5/8/10/15 可选，支持自定义出题要求
- 逐题作答 + 即时判题 + 选项解释 + 正确答案解析
- AI 综合评估报告（分类得分、强弱项、学习建议）

### 4. JD 知识库

- MySQL + Redis Stack（RediSearch）双写
- COSINE 语义检索 + tier/tech_direction 标签过滤
- 向量化失败不阻断入库

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 16+
- MySQL 8.0+
- Redis Stack 7.x

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入数据库、Redis、OSS、AI API Key
```

### 2. 初始化数据库

```bash
mysql -u root -p < resource/init.sql
```

### 3. 启动后端

```bash
uv sync
python main.py
# 服务运行在 http://127.0.0.1:8000
# Swagger 文档：http://127.0.0.1:8000/docs
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:5173
```

## API 概览

| 模块 | 端点前缀 | 端点数 | 说明 |
|------|---------|--------|------|
| 认证 | `/api/auth` | 2 | 注册、登录 |
| 简历 | `/api/resume` | 3 | 上传、查询、分析 |
| 对话 | `/api/conversation` | 7 | 创建、消息（含 SSE 流式）、列表、历史、重命名、删除 |
| 测验 | `/api/quiz` | 7 | 创建+AI 出题、作答、结束+AI 报告、重置、列表、详情、删除 |
| JD 知识库 | `/api/knowledge` | 5 | 录入、批量导入、列表、详情、删除 |

所有 API 统一返回 `{ code: 200, message: "success", data: ... }` 格式。认证方式为 `X-User-Id` 请求头。

## 架构图

```
表现层      Vue 3 SPA（三栏布局 / SSE 流式渲染）
   ↕
接口层      FastAPI RESTful API（StreamingResponse / X-User-Id 鉴权）
   ↕
业务层      Service 层（Resume / Conversation / Message / Quiz / Knowledge）
   ↕
AI 层       LangGraph 6-Node Pipeline + ReAct Agent
            DeepSeek LLM / DashScope Embedding / Tavily Search
   ↕
数据层      MySQL 8 / Redis Stack（向量检索）/ 阿里云 OSS（文件存储）
```

## 许可证

MIT License
