"""数据库模型定义"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from backend.database.db import Base

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Container(Base):
    """容器配置表"""
    __tablename__ = "containers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    cpu = Column(Float, nullable=False)
    memory = Column(Integer, nullable=False)  # MB
    disk = Column(Integer, nullable=False)  # GB
    os_type = Column(String(50))
    os_version = Column(String(50))
    ssh_port = Column(Integer)
    ssh_password = Column(String(100))
    nat_start = Column(Integer, default=0)
    nat_end = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MonitoringData(Base):
    """监控数据表"""
    __tablename__ = "monitoring_data"
    
    id = Column(Integer, primary_key=True, index=True)
    container_name = Column(String(100), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # CPU数据
    cpu_usage = Column(Float)  # 百分比
    load_average = Column(Float)
    
    # 内存数据
    memory_usage = Column(Float)  # MB
    memory_total = Column(Float)  # MB
    memory_percent = Column(Float)  # 百分比
    
    # 网络数据
    network_rx_bytes = Column(Float)  # 接收字节
    network_tx_bytes = Column(Float)  # 发送字节
    network_rx_rate = Column(Float)  # 接收速率 KB/s
    network_tx_rate = Column(Float)  # 发送速率 KB/s
    
    # 磁盘数据
    disk_usage = Column(Float)  # GB
    disk_total = Column(Float)  # GB
    disk_percent = Column(Float)  # 百分比
