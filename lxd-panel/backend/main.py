"""FastAPI主应用程序"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select

from backend.config import settings
from backend.database.db import init_db, AsyncSessionLocal
from backend.database.models import User
from backend.api import auth, containers, monitoring, vnc
from backend.services.monitor_service import monitor_service
from backend.api.auth import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("初始化数据库...")
    await init_db()
    
    # 创建默认管理员账号
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.username == "admin")
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin"),
                is_active=True
            )
            session.add(admin)
            await session.commit()
            print("已创建默认管理员账号: admin/admin")
        else:
            print("管理员账号已存在")
    
    # 启动监控服务
    print("启动监控服务...")
    await monitor_service.start()
    
    yield
    
    # 关闭时执行
    print("停止监控服务...")
    await monitor_service.stop()

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(containers.router, prefix=settings.API_PREFIX)
app.include_router(monitoring.router, prefix=settings.API_PREFIX)
app.include_router(vnc.router, prefix=settings.API_PREFIX)

# 健康检查
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
