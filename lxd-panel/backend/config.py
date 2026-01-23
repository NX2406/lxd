"""配置文件"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "LXD Management Panel"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api"
    
    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./lxd_panel.db"
    
    # 监控配置
    MONITOR_INTERVAL: int = 60  # 采集间隔(秒)
    DATA_RETENTION_HOURS: int = 24  # 数据保留时间(小时)
    
    # LXD配置
    LXD_ENDPOINT: Optional[str] = None  # None表示使用本地Unix socket
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
