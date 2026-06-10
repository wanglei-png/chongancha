"""宠安查 - FastAPI 后端入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import auth, pet, symptom, payment, summary, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化数据库表
    init_db()
    yield
    # 关闭时：清理资源（如有需要）


app = FastAPI(
    title="宠安查 API",
    description="宠物健康助手后端服务",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(pet.router)
app.include_router(symptom.router)
app.include_router(payment.router)
app.include_router(summary.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    """根路径，返回 API 基本信息"""
    return {
        "name": "宠安查 API",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}
