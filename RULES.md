# 1. 文件树

```
career-coach/
├── main.py                      # FastAPI 入口（仅注册路由、生命周期，不含 AI 代码）
├── pyproject.toml               # uv 依赖声明（不再使用 requirements.txt）
├── .env                         # 环境变量（所有配置集中此处）
├── api/                         # 接口层：API 路由
│   ├── auth.py                 # 认证接口（注册、登录）
│   └── chat.py                 # 对话接口
├── core/                        # 核心基础设施（非 AI）
│   ├── config.py               # 全局配置：DB、Redis、OSS
│   ├── database.py             # SQLAlchemy 引擎、会话、Base
│   └── security.py             # 密码哈希等通用安全工具
├── ai/                          # AI 模块（自包含，所有 LangChain 相关代码）
│   ├── __init__.py             # load_dotenv() 触发点
│   ├── config/                 # AI 配置（DeepSeek 等）
│   │   ├── __init__.py         # re-export ai_settings
│   │   └── settings.py         # AISettings 业务类
│   ├── model/                  # 大模型连接
│   │   ├── __init__.py         # 包标识
│   │   └── deepseek.py         # DeepSeek 工厂函数
│   ├── chains/                 # LangChain 链
│   │   └── chat.py             # 对话链
│   ├── agents/                 # LangGraph Agent
│   ├── prompts/                # 提示词模板
│   ├── tools/                  # 自定义工具
│   ├── vectorstore/            # Redis Stack 向量存储
│   └── embeddings/             # 嵌入模型
├── models/                      # 数据模型层：SQLAlchemy ORM
│   └── user.py
├── schemas/                     # 数据校验层：Pydantic
│   ├── response.py             # 统一响应格式
│   ├── user.py                 # 用户请求/响应
│   └── chat.py                 # 对话请求
├── services/                    # 业务逻辑层
│   └── user.py
├── middleware/                  # 中间件：限流、CORS、日志
├── tasks/                       # 异步任务（Celery）
├── tests/
│   ├── test_api/
│   └── test_ai/
├── util/                        # 工具函数
├── resource/                    # 资源文件
│   └── init.sql                # 建库 + 建表脚本
├── frontend/                    # Vue 3 前端
├── 数据库设计.md
├── 接口文档.md
├── 设计文档.md
└── RULES.md
```

# 2. 代码风格

## 2.1 模块分层原则

| 层 | 职责 | 不允许做什么 |
|---|------|-------------|
| `main.py` | 仅 FastAPI 入口（lifespan、路由注册） | 不写任何 AI 相关代码（`load_dotenv` 也不行） |
| `ai/` | 所有 LangChain/LangGraph 代码自成一体 | 配置、模型、链、Agent 等 AI 代码不允许出现在 `ai/` 之外 |
| `core/` | 非 AI 的基础设施：DB / Redis / OSS / 通用安全 | 不依赖 AI 模块 |
| `api/` | 路由 + 请求/响应处理 | 不写业务逻辑 |
| `services/` | 业务逻辑 | 不直接构造 HTTP 响应 |

## 2.2 `__init__.py` 规范

- **`__init__.py` 只能做三件事**：包标识、re-export、必要的初始化副作用（如 `load_dotenv()`）
- 业务代码（类、函数、配置类）必须放在独立的 `.py` 模块中
- 子目录想暴露的对象，在 `__init__.py` 用 `from .xxx import yyy` re-export

```python
# ❌ 不允许：__init__.py 里写业务类
# ai/config/__init__.py
class AISettings(BaseSettings): ...  # 业务代码不允许放这

# ✅ 正确：业务在 settings.py，__init__.py 只 re-export
# ai/config/settings.py
class AISettings(BaseSettings): ...

# ai/config/__init__.py
from ai.config.settings import ai_settings  # noqa: F401
```

## 2.3 文件结构顺序

每个 `.py` 文件按以下顺序组织：

1. **导入语句** — 标准库 → 第三方库 → 项目模块，各组连续书写，中间不空行
2. **模块文档字符串** — 与最后一条 import 之间空一行
3. **代码** — 类、函数、全局变量，紧接 docstring 闭合的 `"""` 之后，不空行

```python
# 1. 导入（标准库/第三方/项目，连续不空行）
from collections.abc import AsyncGenerator
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

# 2. 模块文档字符串（导入后空一行）
"""
数据库引擎、会话工厂、Base 声明
"""
# 3. 代码（紧接 docstring，不空行）
# ── 异步引擎 ──
engine = create_async_engine(...)
```

## 2.4 类型标注

- 所有函数/方法必须标注参数类型和返回类型
- 使用 Python 3.10+ 原生类型：`str`、`int`、`datetime` 等
- 可选类型使用 `Optional[T]` 或 `T | None`
- 异步生成器使用 `AsyncGenerator[YieldType, SendType]`

```python
# ✅
def database_url(self) -> str: ...
async def get_db() -> AsyncGenerator[AsyncSession, Any]: ...

# ❌ 不允许
def database_url(self): ...           # 缺少返回类型
async def get_db() -> AsyncSession:   # yield 函数用错了类型
```

## 2.5 ORM 模型字段定义

- 使用 SQLAlchemy 2.0 Mapped 风格（非经典 Column 风格）
- 主键使用 `BigInteger`（生产环境兼容），`with_variant(Integer, "sqlite")` 兼容测试
- 字符串字段显式指定长度 `String(n)`
- 每个字段必须带 `comment` 参数

```python
id: Mapped[int] = mapped_column(
    BigInteger().with_variant(Integer, "sqlite"),
    primary_key=True, autoincrement=True, comment="主键，用户 ID"
)
username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="登录用户名")
```

## 2.6 异步数据库操作

- 引擎统一使用 `create_async_engine` + `aiomysql`
- 会话通过 `async_sessionmaker` 创建，`expire_on_commit=False`
- FastAPI 依赖注入使用 `async def get_db() -> AsyncGenerator[AsyncSession, Any]`
- 事务处理：成功 commit，异常 rollback，最终 close

## 2.7 配置管理

- 使用 `pydantic-settings` 的 `BaseSettings`
- 字段值统一从 `.env` 加载，**不硬编码**
- 必填配置（如 DB 主机、模型名）不写默认值；可选配置（如 Redis 密码、OSS）可给默认值 `""`
- 多个配置类共享同一份 `.env` 时，必须设置 `extra="ignore"` 忽略不属于自己的字段
- 使用 pydantic v2 风格：`model_config = SettingsConfigDict(...)`，不用过时的 `class Config:`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",                 # 忽略 .env 中不属于本类的字段
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # ── DeepSeek ──
    DEEPSEEK_MODEL: str                  # 必填，无默认值
    DEEPSEEK_TEMPERATURE: float

ai_settings = AISettings()
```

## 2.8 Pydantic 响应/请求模型

- 继承 `pydantic.BaseModel`（非 pydantic-settings 的 `BaseSettings`）
- 字段直接使用类型标注 + 默认值，不套 `Field()` 包装
- 可选数据字段使用 `Optional[Any] = None`
- `@classmethod` 工厂方法的返回类型使用字符串前向引用 `"ClassName"`
- 工厂方法内部使用 docstring 描述用途

```python
from typing import Any, Optional
from pydantic import BaseModel

"""
统一后端返回响应模型
Attributes:
    code: 业务状态码，200 表示成功
    message: 提示信息
    data: 返回数据，可为任意类型
"""
class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "ApiResponse":
        """成功响应快捷方法"""
        return cls(code=200, message=message, data=data)
```

## 2.9 命名约定

| 类别 | 规则 | 示例 |
|------|------|------|
| 模块文件 | snake_case | `database.py`, `user.py`, `deepseek.py` |
| 类名 | PascalCase | `User`, `Base`, `Settings`, `ApiResponse` |
| 函数/方法 | snake_case | `get_db()`, `database_url()`, `get_resume_llm()` |
| 变量 | snake_case | `async_session_factory`, `ai_settings` |
| 环境变量 | UPPER_SNAKE_CASE | `DB_HOST`, `DEEPSEEK_API_KEY` |
| 表名 | 复数 snake_case | `users`, `conversations`, `messages` |
| 不使用缩写 | 见名知义 | `model.py` ✅ / `llm.py` ❌ |

## 2.10 接口路径规范

- 基础前缀 `/api`，**不加版本号 `/v1`**（练手项目无需向后兼容）
- 资源路径用名词复数或单数视语义而定：`/api/auth/login`、`/api/conversation/message`
- 路由的 `prefix` 在 `APIRouter` 构造时定义，不在挂载时重复

```python
# ✅
router = APIRouter(prefix="/api/auth", tags=["认证"])
app.include_router(router)

# ❌ 不允许
router = APIRouter(prefix="/auth")
app.include_router(router, prefix="/api")
```

## 2.11 接口参数传递规范

按参数**语义**选择传递方式，三者各司其职：

| 传递方式 | 适用场景 | 特点 | 示例 |
|---------|---------|------|------|
| Path（路径参数） | 定位唯一资源的主键 ID | 必填、资源标识，缺它接口地址不完整 | `/conversation/{conversation_id}` |
| Query（查询参数） | 筛选、分页、排序、可选过滤条件 | 可有可无，不定位主体资源，只对结果做限制 | `?page=1&page_size=20` |
| Body（请求体） | 创建/修改资源的数据；含大参数时 | JSON 结构，支持长文本 | `{"content": "..."}` |

### 判断规则

1. **GET 请求**：资源 ID 走 Path，筛选/分页/排序走 Query，无 Body
2. **POST 创建资源**：请求体走 Body
3. **POST/PUT 修改资源**：资源 ID 走 Path，修改数据走 Body
4. **DELETE 请求**：资源 ID 走 Path，无 Body
5. **Path 参数位置**：路径参数必须放在路径最后一段，前面用静态路径段表达操作语义

### 大参数说明

内容可能超过 500 字符的长文本字段（消息正文、JD 全文、简历文本等）必须走 Body，避免 URL 长度限制（浏览器/服务器通常 2-8KB）。

```python
# ✅ GET：资源 ID 走 Path（放最后），分页走 Query
@router.get("/messages/{conversation_id}", response_model=ApiResponse)
async def history(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
): ...

# ✅ POST 修改：资源 ID 走 Path（放最后），大参数走 Body
@router.post("/message/{conversation_id}", response_model=ApiResponse)
async def send_msg(
    conversation_id: int,
    req: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
): ...

# ✅ GET 列表：分页走 Query
@router.get("/list", response_model=ApiResponse)
async def list_view(
    page: int = 1,
    page_size: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
): ...

# ❌ 不允许：path 参数不在最后
@router.get("/{conversation_id}/messages")
async def history(conversation_id: int, ...): ...
```

> 注：`Depends()` 注入的依赖项不计入参数统计，只统计业务参数。

## 2.12 接口响应格式

- **所有接口必须返回 `ApiResponse` 格式**
- 流式响应（SSE）由于无法包装，本项目暂不使用，统一一次性返回 JSON

```python
@router.post("", response_model=ApiResponse)
async def chat_endpoint(req: ChatRequest):
    reply = await chat(req.message)
    return ApiResponse.success(data={"reply": reply})
```

## 2.13 垂直间距

| 位置 | 空行数 | 说明 |
|------|--------|------|
| import 与 import 之间 | 0 | 各组导入连续书写，不分行 |
| 最后一条 import 与 docstring | 1 | 导入块与文档字符串之间空一行 |
| docstring 结尾 `"""` 与第一条代码 | 0 | 紧接，不空行 |
| 函数与函数之间 | 1 | 两个顶层函数/类之间空一行 |
| 类方法与方法之间 | 1 | 类内部方法之间空一行 |
| `# ──` 区块注释上方 | 1 | 区块分隔注释前空一行 |
| `# ──` 区块注释下方 | 0 | 区块注释紧接其描述的代码 |

```python
import bcrypt                                         # 导入块，内部不空行

"""
密码哈希与验证
"""
# ── 哈希密码 ──                                     # docstring 后不空行
def hash_password(password: str) -> str:
    return bcrypt.hashpw(...)

# ── 验证密码 ──                                     # 函数间空一行
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(...)
```

# 3. 注释风格

## 3.1 模块文档

- 放在导入语句和代码之间
- 独立的纯字符串，不赋值给 `__doc__`
- 简短描述模块职责

```python
from core.database import Base

"""
用户表
"""
class User(Base):
```

## 3.2 区块分隔

- 代码内逻辑区块使用 `# ── xxx ──` 分隔
- 中文命名

```python
# ── 异步引擎 ──
engine = ...

# ── 异步会话工厂 ──
async_session_factory = ...
```

## 3.3 类/函数注释

- 类上方用 `#` 注释说明用途，简洁一行
- 普通函数/方法内部关键步骤用 `#` 行内注释，不使用内部 docstring
- `@classmethod` 工厂方法作为特例，内部可使用 `"""..."""` docstring

```python
# 所有实体类的基类
class Base(DeclarativeBase):
    pass

# ── FastAPI 依赖：获取数据库会话 ──
async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    # 每个请求获取一个独立数据库会话，请求结束自动关闭
    async with async_session_factory() as session:
```

## 3.4 字段注释

- ORM 字段必须使用 `comment="xxx"`，中文描述
- Pydantic 模型字段直接用类型+默认值，字段说明放在模块 docstring 的 `Attributes:` 区块中，不套 `Field()` 包装

# 4. 数据库设计规范

## 4.1 字段命名

- 字段名一律 snake_case：`user_id`、`created_at`、`last_message_at`
- 时间字段统一以 `_at` 结尾：`created_at` / `updated_at` / `last_login_at`
- 外键字段以 `_id` 结尾，关联表名单数：`user_id` 指向 `users.id`

## 4.2 通用字段

每张业务表都必须包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT` | 主键 |
| `created_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP` | 创建时间 |
| `updated_at` | `DATETIME ON UPDATE CURRENT_TIMESTAMP` | 更新时间（如有可变字段） |

## 4.3 外键策略

- **不使用数据库外键约束**：通过业务代码维护引用关系，便于将来分库分表
- 删除采用应用层级联（业务代码内先删子表再删主表）

## 4.4 冗余字段

允许使用冗余字段加速查询，但需在表设计文档中标注：

```
| message_count | INT UNSIGNED | 0 | 消息总数（冗余字段，加速列表查询） | - |
```

## 4.5 索引

- 高频查询字段必须建索引
- 复合索引按"等值查询 → 范围查询/排序"顺序排列：`(user_id, updated_at DESC)`
- 唯一约束用 `UNIQUE KEY`，普通索引用 `KEY`

## 4.6 字符集

- 数据库、表、字段统一 `utf8mb4` + `utf8mb4_unicode_ci`，支持 emoji 与多语言

# 5. 包管理

- 使用 `uv` 管理依赖，**不使用 `pip` 和 `requirements.txt`**
- 依赖声明在 `pyproject.toml` 的 `[project.dependencies]`
- 安装新包：`uv add <pkg>`，会自动更新 `pyproject.toml` 和 `uv.lock`
