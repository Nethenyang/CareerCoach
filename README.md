# Career Coach

一个基于 FastAPI 后端和 Vue 3 前端的职业教练应用系统，提供用户注册、登录等基础功能。

## 技术栈

### 后端
- **FastAPI** - 现代高性能 Web 框架
- **SQLAlchemy** - 异步 ORM 数据库操作
- **Pydantic** - 数据验证和模型定义
- **Passlib** - 密码哈希加密

### 前端
- **Vue 3** - 渐进式前端框架
- **Vite** - 快速构建工具
- **Pinia** - 状态管理
- **Vue Router** - 路由管理

### 数据库
- **MySQL** - 关系型数据库

## 项目结构

```
├── api/                    # API 路由层
│   └── auth.py            # 认证相关接口
├── core/                  # 核心模块
│   ├── config.py         # 配置管理
│   ├── database.py      # 数据库连接
│   └── security.py      # 安全工具
├── models/                # 数据模型
│   └── user.py          # 用户模型
├── schemas/               # Pydantic 模型
│   ├── response.py     # 响应模型
│   └── user.py         # 用户请求/响应模型
├── services/              # 业务逻辑层
│   └── user.py         # 用户服务
├── middleware/           # 中间件
├── util/                 # 工具函数
├── resource/             # 资源文件
│   └── init.sql        # 数据库初始化脚本
├── frontend/             # 前端应用
│   ├── src/           # 源代码
│   ├── public/       # 静态资源
│   └── package.json  # 前端依赖
├── main.py              # 应用入口
└── requirements.txt    # 后端依赖
```

## 功能特性

- 用户注册
- 用户登录
- 密码安全加密存储
- 异步数据库操作
- RESTful API 设计

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- MySQL 8.0+

### 后端配置

1. 创建虚拟环境并安装依赖：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

2. 配置数据库：

在 `core/config.py` 中修改数据库连接配置：

```python
class Settings(BaseSettings):
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "your_password"
    DATABASE_NAME: str = "career_coach"
```

3. 初始化数据库：

```bash
mysql -u root -p < resource/init.sql
```

4. 启动后端服务：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端配置

1. 安装前端依赖：

```bash
cd frontend
npm install
```

2. 启动开发服务器：

```bash
npm run dev
```

3. 生产环境构建：

```bash
npm run build
```

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |

### 注册接口

**请求：**

```json
{
  "username": "example",
  "password": "password123",
  "nickname": "昵称"
}
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "example",
    "nickname": "昵称"
  }
}
```

### 登录接口

**请求：**

```json
{
  "username": "example",
  "password": "password123"
}
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "example",
    "nickname": "昵称"
  }
}
```

## 开发规范

请参考 [RULES.md](./RULES.md) 了解项目的代码规范，包括：

- 文件结构顺序
- 类型标注规范
- ORM 模型定义规则
- 异步数据库操作规范
- 命名约定
- 注释风格

## 许可证

MIT License