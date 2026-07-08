import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.auth import router as auth_router
from api.conversation import router as conversation_router
from api.resume import router as resume_router
from api.knowledge import router as knowledge_router
from api.quiz import router as quiz_router

"""
FastAPI 应用入口
"""
# ── 日志配置（放在最前，保证子模块 logger 都能输出） ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# ── 应用生命周期 ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    yield
    # 关闭时：释放数据库引擎连接池
    from core.database import engine
    await engine.dispose()

# ── 创建应用 ──
app = FastAPI(
    title="Career Coach",
    version="0.1.0",
    lifespan=lifespan,
)

# ── 注册路由 ──
app.include_router(auth_router)
app.include_router(conversation_router)
app.include_router(resume_router)
app.include_router(knowledge_router)
app.include_router(quiz_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
