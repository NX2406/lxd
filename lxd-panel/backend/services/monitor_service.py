"""监控数据收集服务"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import psutil

from database.db import AsyncSessionLocal
from database.models import MonitoringData
from services.lxd_service import lxd_service
from config import settings

class MonitorService:
    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self._previous_stats = {}  # 存储上一次的网络统计
    
    async def start(self):
        """启动监控服务"""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        print("监控服务已启动")
    
    async def stop(self):
        """停止监控服务"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("监控服务已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                await self._collect_all_containers()
                await self._cleanup_old_data()
                await asyncio.sleep(settings.MONITOR_INTERVAL)
            except Exception as e:
                print(f"监控循环错误: {str(e)}")
                await asyncio.sleep(settings.MONITOR_INTERVAL)
    
    async def _collect_all_containers(self):
        """收集所有容器的监控数据"""
        try:
            containers = lxd_service.get_all_containers()
            async with AsyncSessionLocal() as session:
                for container in containers:
                    if container['status'] == 'Running':
                        await self._collect_container_data(container['name'], session)
                await session.commit()
        except Exception as e:
            print(f"收集监控数据错误: {str(e)}")
    
    async def _collect_container_data(self, container_name: str, session: AsyncSession):
        """收集单个容器的监控数据"""
        try:
            # 获取LXD统计
            stats = lxd_service.get_container_stats(container_name)
            if not stats:
                return
            
            # 通过lxc exec获取容器内部信息
            load_avg = await self._get_container_load(container_name)
            disk_info = await self._get_container_disk(container_name)
            
            # 计算网络速率
            network_rx_rate, network_tx_rate = self._calculate_network_rate(
                container_name, 
                stats['network_rx'], 
                stats['network_tx']
            )
            
            # 创建监控数据记录
            data = MonitoringData(
                container_name=container_name,
                timestamp=datetime.utcnow(),
                cpu_usage=stats.get('cpu_usage', 0),
                load_average=load_avg,
                memory_usage=stats.get('memory_usage', 0),
                memory_total=stats.get('memory_total', 0),
                memory_percent=(stats.get('memory_usage', 0) / stats.get('memory_total', 1)) * 100 if stats.get('memory_total', 0) > 0 else 0,
                network_rx_bytes=stats.get('network_rx', 0),
                network_tx_bytes=stats.get('network_tx', 0),
                network_rx_rate=network_rx_rate,
                network_tx_rate=network_tx_rate,
                disk_usage=disk_info.get('used', 0),
                disk_total=disk_info.get('total', 0),
                disk_percent=disk_info.get('percent', 0)
            )
            
            session.add(data)
        except Exception as e:
            print(f"收集容器 {container_name} 数据错误: {str(e)}")
    
    async def _get_container_load(self, container_name: str) -> float:
        """获取容器负载"""
        try:
            import subprocess
            result = subprocess.run(
                ['lxc', 'exec', container_name, '--', 'cat', '/proc/loadavg'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                load_str = result.stdout.strip().split()[0]
                return float(load_str)
        except Exception:
            pass
        return 0.0
    
    async def _get_container_disk(self, container_name: str) -> Dict:
        """获取容器磁盘使用"""
        try:
            import subprocess
            result = subprocess.run(
                ['lxc', 'exec', container_name, '--', 'df', '-BG', '/'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    total = float(parts[1].replace('G', ''))
                    used = float(parts[2].replace('G', ''))
                    percent = float(parts[4].replace('%', ''))
                    return {'total': total, 'used': used, 'percent': percent}
        except Exception:
            pass
        return {'total': 0, 'used': 0, 'percent': 0}
    
    def _calculate_network_rate(self, container_name: str, rx_bytes: float, tx_bytes: float) -> tuple:
        """计算网络速率 (KB/s)"""
        rx_rate = 0.0
        tx_rate = 0.0
        
        if container_name in self._previous_stats:
            prev = self._previous_stats[container_name]
            time_delta = settings.MONITOR_INTERVAL
            
            rx_rate = (rx_bytes - prev['rx']) / time_delta / 1024  # KB/s
            tx_rate = (tx_bytes - prev['tx']) / time_delta / 1024  # KB/s
        
        self._previous_stats[container_name] = {
            'rx': rx_bytes,
            'tx': tx_bytes
        }
        
        return max(0, rx_rate), max(0, tx_rate)
    
    async def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=settings.DATA_RETENTION_HOURS)
            async with AsyncSessionLocal() as session:
                stmt = delete(MonitoringData).where(MonitoringData.timestamp < cutoff_time)
                await session.execute(stmt)
                await session.commit()
        except Exception as e:
            print(f"清理旧数据错误: {str(e)}")
    
    async def get_current_stats(self, container_name: str) -> Optional[Dict]:
        """获取容器当前统计信息"""
        async with AsyncSessionLocal() as session:
            stmt = select(MonitoringData).where(
                MonitoringData.container_name == container_name
            ).order_by(MonitoringData.timestamp.desc()).limit(1)
            
            result = await session.execute(stmt)
            data = result.scalar_one_or_none()
            
            if data:
                return {
                    'timestamp': data.timestamp.isoformat(),
                    'cpu_usage': data.cpu_usage,
                    'load_average': data.load_average,
                    'memory': {
                        'usage': data.memory_usage,
                        'total': data.memory_total,
                        'percent': data.memory_percent
                    },
                    'network': {
                        'rx_bytes': data.network_rx_bytes,
                        'tx_bytes': data.network_tx_bytes,
                        'rx_rate': data.network_rx_rate,
                        'tx_rate': data.network_tx_rate
                    },
                    'disk': {
                        'usage': data.disk_usage,
                        'total': data.disk_total,
                        'percent': data.disk_percent
                    }
                }
            return None
    
    async def get_history_stats(self, container_name: str, hours: int = 24) -> list:
        """获取容器历史统计信息"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        async with AsyncSessionLocal() as session:
            stmt = select(MonitoringData).where(
                MonitoringData.container_name == container_name,
                MonitoringData.timestamp >= start_time
            ).order_by(MonitoringData.timestamp.asc())
            
            result = await session.execute(stmt)
            data_list = result.scalars().all()
            
            return [{
                'timestamp': data.timestamp.isoformat(),
                'cpu_usage': data.cpu_usage,
                'load_average': data.load_average,
                'memory_percent': data.memory_percent,
                'network_rx_rate': data.network_rx_rate,
                'network_tx_rate': data.network_tx_rate,
                'disk_percent': data.disk_percent
            } for data in data_list]

# 全局监控服务实例
monitor_service = MonitorService()
