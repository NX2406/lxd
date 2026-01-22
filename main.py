"""
LXD 管理面板 - FastAPI 主应用
完整后端代码（包含所有功能）
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import psutil
import uvicorn
import secrets
import os

# ==================== 导入模块（所有代码整合在本文件）====================

from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import subprocess
import json
import re

# ==================== 配置 ====================

class Settings(BaseSettings):
    APP_NAME: str = "LXD 管理面板"
    VERSION: str = "1.0.0"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DATABASE_URL: str = "sqlite:///./data/lxd_panel.db"
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ADMIN_CHAT_ID: Optional[str] = None
    MONITOR_INTERVAL_SECONDS: int = 60
    DATA_RETENTION_DAYS: int = 30
    CPU_ALERT_THRESHOLD: float = 80.0
    
    class Config:
        env_file = ".env"

settings = Settings()

# ==================== 数据库 ====================

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 数据模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    api_key = Column(String(100), unique=True, index=True)
    telegram_id = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    containers = relationship("Container", back_populates="user")

class Container(Base):
    __tablename__ = "containers"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    cpu = Column(Float)
    memory = Column(Integer)
    disk = Column(Integer)
    ssh_port = Column(Integer)
    nat_start = Column(Integer, nullable=True)
    nat_end = Column(Integer, nullable=True)
    os_type = Column(String(50))
    os_version = Column(String(50))
    root_password = Column(String(100))
    status = Column(String(20), default="Stopped")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="containers")
    monitor_data = relationship("MonitorData", back_populates="container")

class MonitorData(Base):
    __tablename__ = "monitor_data"
    id = Column(Integer, primary_key=True)
    container_id = Column(Integer, ForeignKey("containers.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    network_in = Column(Float, nullable=True)
    network_out = Column(Float, nullable=True)
    container = relationship("Container", back_populates="monitor_data")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    alert_type = Column(String(50))
    message = Column(Text)
    container_id = Column(Integer, nullable=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True)
    action = Column(String(100))
    user_id = Column(Integer, nullable=True)
    container_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 初始化数据库
def init_db():
    Base.metadata.create_all(bind=engine)
    
    # 创建管理员密码哈希（存储在环境变量或配置文件）
    db = SessionLocal()
    try:
        # 注：管理员密码直接硬编码验证，不存储在数据库
        pass
    finally:
        db.close()

# ==================== Pydantic 模型 ====================

class UserCreate(BaseModel):
    username: str
    telegram_id: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    api_key: str
    is_active: bool
    
    class Config:
        from_attributes = True

class ContainerCreate(BaseModel):
    name: str
    cpu: float
    memory: int
    disk: int
    ssh_port: int
    nat_start: Optional[int] = None
    nat_end: Optional[int] = None
    os_type: str
    os_version: str

class ContainerResponse(BaseModel):
    id: int
    name: str
    user_id: Optional[int]
    cpu: float
    memory: int
    status: str
    ssh_port: int
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ==================== 认证 ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = pwd_context.hash("admin123")  # 默认密码

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("sub") != ADMIN_USERNAME:
            raise HTTPException(status_code=401)
        return {"username": ADMIN_USERNAME}
    except:
        raise HTTPException(status_code=401, detail="认证失败")

def generate_api_key():
    return secrets.token_urlsafe(32)

# ==================== LXD 服务 ====================

class LXDService:
    @staticmethod
    def run_command(cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip()
        except:
            return False, ""
    
    @staticmethod
    def list_containers():
        success, output = LXDService.run_command(["lxc", "list", "--format", "json"])
        if success:
            try:
                return json.loads(output)
            except:
                return []
        return []
    
    @staticmethod
    def start_container(name):
        success, _ = LXDService.run_command(["lxc", "start", name])
        return success
    
    @staticmethod
    def stop_container(name):
        success, _ = LXDService.run_command(["lxc", "stop", name])
        return success
    
    @staticmethod
    def restart_container(name):
        success, _ = LXDService.run_command(["lxc", "restart", name])
        return success
    
    @staticmethod
    def get_host_ip():
        """获取宿主机 IP"""
        success, output = LXDService.run_command(["ip", "addr", "show"])
        if success:
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+).*global', output)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def add_port_mapping(container_name, container_ip, host_ip, external_port, internal_port, protocol="tcp"):
        """添加端口映射"""
        device_name = f"proxy-{protocol}-{external_port}"
        listen = f"{protocol}:{host_ip}:{external_port}"
        connect = f"{protocol}:{container_ip}:{internal_port}"
        
        success, _ = LXDService.run_command([
            "lxc", "config", "device", "add", container_name,
            device_name, "proxy",
            f"listen={listen}",
            f"connect={connect}",
            "nat=true"
        ])
        return success
    
    @staticmethod
    def rebuild_container(name, image):
        """重装容器系统"""
        LXDService.stop_container(name)
        success, _ = LXDService.run_command(["lxc", "rebuild", name, image])
        if success:
            LXDService.start_container(name)
        return success
    
    @staticmethod
    def delete_container(name):
        """删除容器"""
        LXDService.stop_container(name)
        success, _ = LXDService.run_command(["lxc", "delete", name, "--force"])
        return success

# ==================== FastAPI 应用 ====================

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== API 路由 ====================

@app.post("/api/admin/login", response_model=Token)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """管理员登录"""
    if data.username != ADMIN_USERNAME or not pwd_context.verify(data.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    
    token = create_access_token({"sub": ADMIN_USERNAME})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/admin/users", dependencies=[Depends(get_current_admin)])
async def list_users(db: Session = Depends(get_db)):
    """获取用户列表"""
    users = db.query(User).all()
    return users

@app.post("/api/admin/users", dependencies=[Depends(get_current_admin)])
async def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """创建用户"""
    api_key = generate_api_key()
    hashed_key = pwd_context.hash(api_key)
    
    user = User(username=data.username, api_key=hashed_key, telegram_id=data.telegram_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 返回明文 API Key（仅此一次）
    return {"id": user.id, "username": user.username, "api_key": api_key}

@app.get("/api/admin/containers", dependencies=[Depends(get_current_admin)])
async def list_containers(db: Session = Depends(get_db)):
    """获取所有容器"""
    containers = db.query(Container).all()
    
    # 同步 LXD 状态
    lxd_containers = LXDService.list_containers()
    lxd_status_map = {c['name']: c['status'] for c in lxd_containers}
    
    for container in containers:
        if container.name in lxd_status_map:
            container.status = lxd_status_map[container.name]
    
    db.commit()
    return containers

@app.post("/api/admin/containers", dependencies=[Depends(get_current_admin)])
async def create_container(data: ContainerCreate, db: Session = Depends(get_db)):
    """创建容器（真实创建 LXD 容器）"""
    # 检查名称是否已存在
    if db.query(Container).filter(Container.name == data.name).first():
        raise HTTPException(status_code=400, detail="容器名称已存在")
    
    # 构建镜像名称
    if data.os_type and data.os_version:
        image = f"images:{data.os_type}/{data.os_version}"
    else:
        image = "images:debian/12"
    
    # 检查镜像是否存在
    success, _ = LXDService.run_command(["lxc", "image", "list", image])
    if not success:
        raise HTTPException(status_code=400, detail="镜像不存在")
    
    # 创建容器配置
    cpu_config = []
    if "." in str(data.cpu):
        cpu_count = int(float(data.cpu) + 0.99)
        cpu_allowance = int(float(data.cpu) * 100 / cpu_count)
        cpu_config = ["-c", f"limits.cpu={cpu_count}", "-c", f"limits.cpu.allowance={cpu_allowance}%"]
    else:
        cpu_config = ["-c", f"limits.cpu={data.cpu}"]
    
    # 执行创建命令
    cmd = ["lxc", "init", image, data.name] + cpu_config + [
        "-c", f"limits.memory={data.memory}MiB",
        "-c", "limits.processes=500",
        "-c", "security.nesting=true",
        "-c", "security.privileged=false"
    ]
    
    success, output = LXDService.run_command(cmd)
    if not success:
        raise HTTPException(status_code=500, detail=f"创建失败: {output}")
    
    # 配置存储
    if data.disk:
        disk_mb = int(data.disk * 1024)
        LXDService.run_command(["lxc", "config", "device", "override", data.name, "root", f"size={disk_mb}MB"])
    
    # 启动容器
    LXDService.start_container(data.name)
    
    # 生成随机密码
    root_password = secrets.token_urlsafe(8)
    
    # 等待容器启动并配置
    import time
    time.sleep(5)
    
    # 设置 root 密码
    LXDService.run_command(["lxc", "exec", data.name, "--", "sh", "-c", f"echo 'root:{root_password}' | chpasswd"])
    
    # 获取容器 IP
    container_ip = None
    for i in range(10):
        time.sleep(2)
        success, output = LXDService.run_command(["lxc", "list", data.name, "--format", "json"])
        if success:
            try:
                containers = json.loads(output)
                if containers and containers[0].get("state", {}).get("network"):
                    eth0 = containers[0]["state"]["network"].get("eth0", {})
                    for addr in eth0.get("addresses", []):
                        if addr.get("family") == "inet":
                            container_ip = addr.get("address")
                            break
                if container_ip:
                    break
            except:
                pass
    
    if not container_ip:
        raise HTTPException(status_code=500, detail="无法获取容器 IP")
    
    # 配置端口映射
    host_ip = LXDService.get_host_ip()
    if host_ip and data.ssh_port:
        LXDService.add_port_mapping(data.name, container_ip, host_ip, data.ssh_port, 22, "tcp")
    
    # 保存到数据库
    container = Container(
        name=data.name,
        cpu=data.cpu,
        memory=data.memory,
        disk=data.disk,
        ssh_port=data.ssh_port,
        nat_start=data.nat_start,
        nat_end=data.nat_end,
        os_type=data.os_type,
        os_version=data.os_version,
        root_password=root_password,
        status="Running"
    )
    db.add(container)
    db.commit()
    db.refresh(container)
    
    return {
        "id": container.id,
        "name": container.name,
        "root_password": root_password,
        "container_ip": container_ip,
        "ssh_port": data.ssh_port
    }

@app.post("/api/containers/{container_id}/start")
async def start_container_api(container_id: int, db: Session = Depends(get_db)):
    """启动容器"""
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404)
    
    if LXDService.start_container(container.name):
        container.status = "Running"
        db.commit()
        return {"message": "启动成功"}
    raise HTTPException(status_code=500, detail="启动失败")

@app.post("/api/containers/{container_id}/stop")
async def stop_container_api(container_id: int, db: Session = Depends(get_db)):
    """停止容器"""
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404)
    
    if LXDService.stop_container(container.name):
        container.status = "Stopped"
        db.commit()
        return {"message": "停止成功"}
    raise HTTPException(status_code=500, detail="停止失败")

@app.post("/api/containers/{container_id}/restart")
async def restart_container_api(container_id: int, db: Session = Depends(get_db)):
    """重启容器"""
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404)
    
    if LXDService.restart_container(container.name):
        return {"message": "重启成功"}
    raise HTTPException(status_code=500, detail="重启失败")

@app.post("/api/containers/{container_id}/rebuild")
async def rebuild_container_api(container_id: int, os_type: str, os_version: str, db: Session = Depends(get_db)):
    """重装容器系统"""
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404)
    
    image = f"images:{os_type}/{os_version}"
    if LXDService.rebuild_container(container.name, image):
        # 更新数据库
        container.os_type = os_type
        container.os_version = os_version
        new_password = secrets.token_urlsafe(8)
        container.root_password = new_password
        db.commit()
        
        return {"message": "重装成功", "new_password": new_password}
    raise HTTPException(status_code=500, detail="重装失败")

@app.delete("/api/containers/{container_id}")
async def delete_container_api(container_id: int, db: Session = Depends(get_db)):
    """删除容器"""
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404)
    
    if LXDService.delete_container(container.name):
        db.delete(container)
        db.commit()
        return {"message": "删除成功"}
    raise HTTPException(status_code=500, detail="删除失败")

@app.post("/api/containers/{container_id}/ports")
async def add_port_mapping_api(container_id: int, external_port: int, internal_port: int, protocol: str = "tcp", db: Session = Depends(get_db)):
    """添加端口映射"""
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404)
    
    # 获取容器 IP
    success, output = LXDService.run_command(["lxc", "list", container.name, "--format", "json"])
    if not success:
        raise HTTPException(status_code=500, detail="无法获取容器信息")
    
    try:
        containers = json.loads(output)
        container_ip = None
        if containers:
            eth0 = containers[0].get("state", {}).get("network", {}).get("eth0", {})
            for addr in eth0.get("addresses", []):
                if addr.get("family") == "inet":
                    container_ip = addr.get("address")
                    break
    except:
        raise HTTPException(status_code=500, detail="解析容器 IP 失败")
    
    if not container_ip:
        raise HTTPException(status_code=500, detail="容器未获取到 IP")
    
    host_ip = LXDService.get_host_ip()
    if not host_ip:
        raise HTTPException(status_code=500, detail="无法获取宿主机 IP")
    
    if LXDService.add_port_mapping(container.name, container_ip, host_ip, external_port, internal_port, protocol):
        return {"message": "端口映射添加成功"}
    raise HTTPException(status_code=500, detail="添加失败")

@app.get("/api/system/stats", dependencies=[Depends(get_current_admin)])
async def get_system_stats(db: Session = Depends(get_db)):
    """获取系统统计"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    total_containers = db.query(Container).count()
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_total": round(memory.total / 1024**3, 2),
        "memory_used": round(memory.used / 1024**3, 2),
        "disk_percent": disk.percent,
        "disk_total": round(disk.total / 1024**3, 2),
        "disk_used": round(disk.used / 1024**3, 2),
        "container_count": total_containers
    }

# ==================== 静态文件和前端 ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回管理员前端页面"""
    html_path = "frontend/admin/index.html"
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>LXD 管理面板</h1><p>前端文件未找到</p>"

# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    init_db()
    print(f"✅ {settings.APP_NAME} v{settings.VERSION} 启动成功")
    print(f"📊 访问: http://0.0.0.0:8000")

# ==================== 主程序 ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
