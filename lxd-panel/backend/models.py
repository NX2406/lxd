from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class InstanceInfo(BaseModel):
    """实例基本信息"""
    name: str
    status: str
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    architecture: str
    created_at: Optional[datetime] = None
    description: Optional[str] = None


class ResourceUsage(BaseModel):
    """资源使用情况"""
    cpu_percent: float = Field(..., ge=0, le=100, description="CPU使用率")
    memory_used: int = Field(..., ge=0, description="已使用内存(MB)")
    memory_total: int = Field(..., ge=0, description="总内存(MB)")
    disk_used: int = Field(..., ge=0, description="已使用磁盘(MB)")
    disk_total: int = Field(..., ge=0, description="总磁盘(MB)")
    network_rx: int = Field(default=0, description="网络接收(MB)")
    network_tx: int = Field(default=0, description="网络发送(MB)")


class InstanceDetail(BaseModel):
    """实例详细信息"""
    info: InstanceInfo
    resources: ResourceUsage
    ssh_port: Optional[int] = None
    nat_ports: Optional[str] = None
    root_password: Optional[str] = None


class CreateInstanceRequest(BaseModel):
    """创建实例请求"""
    name: str = Field(..., pattern=r'^[a-zA-Z0-9-]+$', description="实例名称")
    os_type: str = Field(default="debian", description="操作系统类型")
    os_version: str = Field(default="12", description="操作系统版本")
    cpu: float = Field(default=1.0, ge=0.5, description="CPU核数")
    memory: int = Field(default=512, ge=256, description="内存大小(MB)")
    disk: int = Field(default=10, ge=2, description="磁盘大小(GB)")
    ssh_port: int = Field(default=20001, ge=1024, le=65535, description="SSH端口")
    nat_start: int = Field(default=0, ge=0, le=65535, description="NAT起始端口")
    nat_end: int = Field(default=0, ge=0, le=65535, description="NAT结束端口")
    bandwidth: int = Field(default=100, ge=1, description="带宽限制(Mbps)")


class OperationResponse(BaseModel):
    """操作响应"""
    success: bool
    message: str
    data: Optional[Dict] = None


class WSMessage(BaseModel):
    """WebSocket消息"""
    type: str  # "instance_update", "resource_update", "error"
    data: Dict
    timestamp: datetime = Field(default_factory=datetime.now)
