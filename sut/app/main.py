import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.utils.exceptions import BizError, biz_error_handler, global_exception_handler
from app.middleware.logging import request_logging_middleware
from app.routes import auth, users, projects, tasks, stats

logger = logging.getLogger("taskflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")
    yield
    logger.info("TaskFlow 关闭")


app = FastAPI(
    title="TaskFlow",
    description="任务流管理平台 — 支持团队协作、任务管理、项目管理、数据统计",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
app.middleware("http")(request_logging_middleware)

# 全局异常处理
app.add_exception_handler(BizError, biz_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 注册路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(stats.router)


@app.get("/")
def root():
    return {"code": 200, "msg": "TaskFlow is running", "data": None}


@app.get("/health")
def health():
    return {"status": "ok"}
