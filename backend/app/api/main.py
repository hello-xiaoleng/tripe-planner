"""FastAPI应用主入口"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import trip

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("智能旅行助手启动中...")
    yield
    logger.info("智能旅行助手关闭")


# 创建FastAPI应用
app = FastAPI(
    title="智能旅行助手 API",
    description="基于AI的个性化旅行规划服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trip.router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "智能旅行助手",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
