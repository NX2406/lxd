#!/usr/bin/env python3
"""
LXD管理面板 - 后端API服务
提供RESTful API和WebSocket接口用于LXD实例管理和实时监控
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict
import asyncio
import uvicorn
import logging
from datetime import datetime

from models import (
    InstanceInfo, InstanceDetail, CreateInstanceRequest,
    OperationResponse, WSMessage
)
from lxd_manager import LXDManager
from auth import verify_api_key, generate_api_key, set_api_key

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="LXD管理面板API",
    description="LXD实例管理与监控API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LXD管理器实例
lxd_manager = LXDManager()

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")

manager = ConnectionManager()


# ========== API端点 ==========

@app.get("/", tags=["基础"])
async def root():
    """API根路径"""
    return {
        "name": "LXD管理面板API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health", tags=["基础"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "lxd_connected": lxd_manager.client is not None
    }


@app.get("/api/instances", response_model=List[InstanceInfo], tags=["实例管理"])
async def get_instances():
    """获取所有实例列表"""
    try:
        instances = lxd_manager.get_all_instances()
        return instances
    except Exception as e:
        logger.error(f"获取实例列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/instances/{name}", response_model=InstanceDetail, tags=["实例管理"])
async def get_instance_detail(name: str):
    """获取单个实例详细信息"""
    detail = lxd_manager.get_instance_detail(name)
    if not detail:
        raise HTTPException(status_code=404, detail=f"实例 {name} 不存在")
    return detail


@app.post("/api/instances/{name}/start", response_model=OperationResponse, tags=["实例操作"])
async def start_instance(name: str):
    """启动实例"""
    success = lxd_manager.start_instance(name)
    return OperationResponse(
        success=success,
        message=f"实例 {name} 启动{'成功' if success else '失败'}"
    )


@app.post("/api/instances/{name}/stop", response_model=OperationResponse, tags=["实例操作"])
async def stop_instance(name: str):
    """停止实例"""
    success = lxd_manager.stop_instance(name)
    return OperationResponse(
        success=success,
        message=f"实例 {name} 停止{'成功' if success else '失败'}"
    )


@app.post("/api/instances/{name}/restart", response_model=OperationResponse, tags=["实例操作"])
async def restart_instance(name: str):
    """重启实例"""
    success = lxd_manager.restart_instance(name)
    return OperationResponse(
        success=success,
        message=f"实例 {name} 重启{'成功' if success else '失败'}"
    )


@app.delete("/api/instances/{name}", response_model=OperationResponse, tags=["实例操作"])
async def delete_instance(name: str, force: bool = False):
    """删除实例"""
    success = lxd_manager.delete_instance(name, force)
    return OperationResponse(
        success=success,
        message=f"实例 {name} 删除{'成功' if success else '失败'}"
    )


@app.get("/api/host/info", tags=["系统信息"])
async def get_host_info():
    """获取宿主机信息"""
    return lxd_manager.get_host_info()


@app.get("/api/instances/{name}/resources", tags=["监控"])
async def get_instance_resources(name: str):
    """获取实例资源使用情况"""
    detail = lxd_manager.get_instance_detail(name)
    if not detail:
        raise HTTPException(status_code=404, detail=f"实例 {name} 不存在")
    return detail.resources


# ========== WebSocket端点 ==========

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket实时监控端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 获取所有实例信息
            instances = lxd_manager.get_all_instances()
            
            # 获取详细资源信息
            instances_data = []
            for inst in instances:
                detail = lxd_manager.get_instance_detail(inst.name)
                if detail:
                    instances_data.append({
                        "name": detail.info.name,
                        "status": detail.info.status,
                        "ipv4": detail.info.ipv4,
                        "resources": detail.resources.dict(),
                        "ssh_port": detail.ssh_port,
                        "nat_ports": detail.nat_ports
                    })
            
            # 获取宿主机信息
            host_info = lxd_manager.get_host_info()
            
            # 发送数据
            await websocket.send_json({
                "type": "update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "instances": instances_data,
                    "host": host_info
                }
            })
            
            # 等待5秒后更新
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)


# ========== 启动配置 ==========

if __name__ == "__main__":
    # 可以从环境变量或配置文件读取
    import os
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    # 加载API密钥
    api_key_file = "/opt/lxd-panel/api_key.txt"
    if os.path.exists(api_key_file):
        with open(api_key_file, 'r') as f:
            set_api_key(f.read().strip())
    
    logger.info(f"启动LXD管理面板API服务 - {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
