"""容器API路由"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.models import User
from services.lxd_service import lxd_service
from api.auth import get_current_user

router = APIRouter(prefix="/containers", tags=["容器管理"])

# Pydantic模型
class ContainerCreate(BaseModel):
    name: str
    cpu: float
    memory: int
    disk: int
    os_type: str
    os_version: str
    ssh_port: int
    nat_start: int = 0
    nat_end: int = 0
    bandwidth: int = 10

class ContainerInfo(BaseModel):
    name: str
    status: str
    ip: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[int] = None
    disk: Optional[int] = None
    ssh_port: Optional[int] = None

class MessageResponse(BaseModel):
    message: str

# API路由
@router.get("", response_model=List[ContainerInfo])
async def list_containers(current_user: User = Depends(get_current_user)):
    """获取所有容器列表"""
    return lxd_service.get_all_containers()

@router.post("", response_model=MessageResponse)
async def create_container(
    config: ContainerCreate,
    current_user: User = Depends(get_current_user)
):
    """
    创建容器 - 完全通过Web面板实现
    """
    try:
        from services.container_creator import container_creator
        
        # 验证容器名是否已存在
        existing = lxd_service.get_container(config.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"容器 {config.name} 已存在")
        
        # 调用创建服务（同步调用，因为需要返回密码等信息）
        result = container_creator.create_container(
            name=config.name,
            cpu=config.cpu,
            memory=config.memory,
            disk=config.disk,
            os_type=config.os_type,
            os_version=config.os_version,
            ssh_port=config.ssh_port,
            nat_start=config.nat_start,
            nat_end=config.nat_end,
            bandwidth=config.bandwidth
        )
        
        if result['success']:
            # 返回包含密码等重要信息的详细消息
            data = result.get('data', {})
            message = f"容器创建成功！\n\n连接信息：\nIP: {data.get('ip', 'N/A')}\nSSH端口: {data.get('ssh_port', 22)}\nroot密码: {data.get('password', 'N/A')}\n\n请妥善保管密码！"
            return {"message": message}
        else:
            raise HTTPException(status_code=500, detail=result['message'])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建容器失败: {str(e)}")

@router.post("/{name}/start", response_model=MessageResponse)
async def start_container(name: str, current_user: User = Depends(get_current_user)):
    """启动容器"""
    result = lxd_service.start_container(name)
    if result:
        return {"message": f"容器 {name} 启动成功"}
    raise HTTPException(status_code=500, detail="启动失败")

@router.post("/{name}/stop", response_model=MessageResponse)
async def stop_container(name: str, current_user: User = Depends(get_current_user)):
    """停止容器"""
    result = lxd_service.stop_container(name)
    if result:
        return {"message": f"容器 {name} 停止成功"}
    raise HTTPException(status_code=500, detail="停止失败")

@router.post("/{name}/restart", response_model=MessageResponse)
async def restart_container(name: str, current_user: User = Depends(get_current_user)):
    """重启容器"""
    result = lxd_service.restart_container(name)
    if result:
        return {"message": f"容器 {name} 重启成功"}
    raise HTTPException(status_code=500, detail="重启失败")

@router.delete("/{name}", response_model=MessageResponse)
async def delete_container(name: str, current_user: User = Depends(get_current_user)):
    """删除容器"""
    result = lxd_service.delete_container(name)
    if result:
        return {"message": f"容器 {name} 删除成功"}
    raise HTTPException(status_code=500, detail="删除失败")

@router.get("/{name}", response_model=ContainerInfo)
async def get_container(name: str, current_user: User = Depends(get_current_user)):
    """获取容器详情"""
    container = lxd_service.get_container(name)
    if container:
        return container
    raise HTTPException(status_code=404, detail="容器不存在")
