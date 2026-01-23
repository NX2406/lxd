"""监控数据API路由"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json

from database.models import User
from services.monitor_service import monitor_service
from api.auth import get_current_user

router = APIRouter(prefix="/monitoring", tags=["监控"])

# API路由
@router.get("/{name}/current")
async def get_current_stats(name: str, current_user: User = Depends(get_current_user)):
    """获取容器当前资源使用情况"""
    try:
        stats = await monitor_service.get_current_stats(name)
        if not stats:
            raise HTTPException(status_code=404, detail="没有找到监控数据")
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控数据失败: {str(e)}")

@router.get("/{name}/history")
async def get_history_stats(name: str, hours: int = 24, current_user: User = Depends(get_current_user)):
    """获取容器历史监控数据"""
    try:
        if hours < 1 or hours > 24:
            raise HTTPException(status_code=400, detail="小时数必须在1-24之间")
        
        stats = await monitor_service.get_history_stats(name, hours)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")

@router.websocket("/ws/{name}")
async def monitoring_websocket(websocket: WebSocket, name: str):
    """实时监控数据WebSocket"""
    await websocket.accept()
    
    try:
        while True:
            # 获取最新数据
            stats = await monitor_service.get_current_stats(name)
            if stats:
                await websocket.send_json(stats)
            
            # 每5秒推送一次
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print(f"WebSocket断开连接: {name}")
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        await websocket.close()
