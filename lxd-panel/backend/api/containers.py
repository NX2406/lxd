"""容器管理API路由"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.database.models import User
from backend.services.lxd_service import lxd_service
from backend.api.auth import get_current_user

router = APIRouter(prefix="/containers", tags=["容器管理"])

# Pydantic模型
class ContainerInfo(BaseModel):
    name: str
    status: str
    ip_address: Optional[str]
    cpu: str
    memory: int
    ssh_port: Optional[str]
    password: Optional[str]
    nat_start: Optional[int]
    nat_end: Optional[int]
    architecture: str
    created_at: Optional[str]

class ContainerCreate(BaseModel):
    name: str = Field(..., pattern=r'^[a-zA-Z0-9-]+$')
    cpu: float = Field(1.0, gt=0, le=64)
    memory: int = Field(512, gt=128, le=65536)  # MB
    disk: int = Field(2, gt=1, le=1000)  # GB
    os_type: str = Field("debian", min_length=1)
    os_version: str = Field("12", min_length=1)
    ssh_port: int = Field(20001, gt=1024, le=65535)
    nat_start: int = Field(0, ge=0, le=65535)
    nat_end: int = Field(0, ge=0, le=65535)
    bandwidth: int = Field(10, gt=0, le=10000)  # MB/s

class ContainerRebuild(BaseModel):
    os_type: str
    os_version: str

class MessageResponse(BaseModel):
    message: str

# API路由
@router.get("", response_model=List[ContainerInfo])
async def list_containers(current_user: User = Depends(get_current_user)):
    """获取所有容器列表"""
    try:
        containers = lxd_service.get_all_containers()
        return containers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取容器列表失败: {str(e)}")

@router.get("/{name}", response_model=ContainerInfo)
async def get_container(name: str, current_user: User = Depends(get_current_user)):
    """获取单个容器信息"""
    container = lxd_service.get_container(name)
    if not container:
        raise HTTPException(status_code=404, detail="容器不存在")
    return container

@router.post("", response_model=MessageResponse)
async def create_container(
    config: ContainerCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    创建容器 (通过bash脚本)
    注意: 这个功能需要调用原有的bash脚本
    """
    raise HTTPException(
        status_code=501, 
        detail="容器创建功能需要通过原有bash脚本实现, 请使用命令行创建或等待集成完成"
    )

@router.post("/{name}/start", response_model=MessageResponse)
async def start_container(name: str, current_user: User = Depends(get_current_user)):
    """启动容器"""
    try:
        lxd_service.start_container(name)
        return {"message": f"容器 {name} 已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/stop", response_model=MessageResponse)
async def stop_container(name: str, current_user: User = Depends(get_current_user)):
    """停止容器"""
    try:
        lxd_service.stop_container(name)
        return {"message": f"容器 {name} 已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/restart", response_model=MessageResponse)
async def restart_container(name: str, current_user: User = Depends(get_current_user)):
    """重启容器"""
    try:
        lxd_service.restart_container(name)
        return {"message": f"容器 {name} 已重启"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/rebuild", response_model=MessageResponse)
async def rebuild_container(
    name: str,
    config: ContainerRebuild,
    current_user: User = Depends(get_current_user)
):
    """重装容器系统"""
    try:
        lxd_service.rebuild_container(name, config.os_type, config.os_version)
        return {"message": f"容器 {name} 系统重装成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{name}", response_model=MessageResponse)
async def delete_container(name: str, current_user: User = Depends(get_current_user)):
    """删除容器"""
    try:
        lxd_service.delete_container(name)
        return {"message": f"容器 {name} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
