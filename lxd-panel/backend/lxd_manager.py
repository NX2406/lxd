import pylxd
import psutil
import time
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from models import InstanceInfo, ResourceUsage, InstanceDetail


class LXDManager:
    """LXD管理器 - 与LXD进行交互"""
    
    def __init__(self):
        try:
            self.client = pylxd.Client()
        except Exception as e:
            print(f"LXD连接失败: {e}")
            self.client = None
    
    def get_all_instances(self) -> List[InstanceInfo]:
        """获取所有实例列表"""
        if not self.client:
            return []
        
        instances = []
        try:
            for container in self.client.containers.all():
                ipv4 = self._get_container_ipv4(container)
                instances.append(InstanceInfo(
                    name=container.name,
                    status=container.status,
                    ipv4=ipv4,
                    ipv6=None,  # 可选扩展
                    architecture=container.architecture,
                    created_at=container.created_at,
                    description=container.description
                ))
        except Exception as e:
            print(f"获取实例列表失败: {e}")
        
        return instances
    
    def get_instance_detail(self, name: str) -> Optional[InstanceDetail]:
        """获取单个实例的详细信息"""
        try:
            container = self.client.containers.get(name)
            
            # 基本信息
            ipv4 = self._get_container_ipv4(container)
            info = InstanceInfo(
                name=container.name,
                status=container.status,
                ipv4=ipv4,
                architecture=container.architecture,
                created_at=container.created_at,
                description=container.description
            )
            
            # 资源使用情况
            resources = self._get_instance_resources(container)
            
            # 从description解析SSH端口和密码
            ssh_port, nat_ports, password = self._parse_description(container.description)
            
            return InstanceDetail(
                info=info,
                resources=resources,
                ssh_port=ssh_port,
                nat_ports=nat_ports,
                root_password=password
            )
        except Exception as e:
            print(f"获取实例详情失败: {e}")
            return None
    
    def _get_container_ipv4(self, container) -> Optional[str]:
        """获取容器IPv4地址"""
        try:
            if container.status != 'Running':
                return None
            state = container.state()
            network = state.network
            if 'eth0' in network and network['eth0']['addresses']:
                for addr in network['eth0']['addresses']:
                    if addr['family'] == 'inet':
                        return addr['address']
        except:
            pass
        return None
    
    def _get_instance_resources(self, container) -> ResourceUsage:
        """获取实例资源使用情况"""
        try:
            if container.status != 'Running':
                # 未运行时返回0
                config = container.config
                memory_total = self._parse_memory_limit(config.get('limits.memory', '512MiB'))
                return ResourceUsage(
                    cpu_percent=0.0,
                    memory_used=0,
                    memory_total=memory_total,
                    disk_used=0,
                    disk_total=10240,  # 默认10GB
                    network_rx=0,
                    network_tx=0
                )
            
            state = container.state()
            
            # CPU使用率
            cpu_usage = state.cpu.get('usage', 0)
            cpu_percent = min(cpu_usage / 10000000, 100.0)  # 转换为百分比
            
            # 内存
            memory = state.memory
            memory_used = memory.get('usage', 0) // (1024 * 1024)  # 转换为MB
            memory_total = memory.get('usage_peak', 512) // (1024 * 1024)
            
            # 从config获取内存限制
            config = container.config
            memory_total = self._parse_memory_limit(config.get('limits.memory', '512MiB'))
            
            # 磁盘 (简化处理)
            disk_used = 0
            disk_total = 10240  # 默认10GB
            try:
                devices = container.devices
                if 'root' in devices:
                    size_str = devices['root'].get('size', '10GB')
                    disk_total = self._parse_disk_size(size_str)
            except:
                pass
            
            # 网络流量
            network_rx = 0
            network_tx = 0
            try:
                if 'eth0' in state.network:
                    counters = state.network['eth0']['counters']
                    network_rx = counters.get('bytes_received', 0) // (1024 * 1024)  # MB
                    network_tx = counters.get('bytes_sent', 0) // (1024 * 1024)  # MB
            except:
                pass
            
            return ResourceUsage(
                cpu_percent=round(cpu_percent, 2),
                memory_used=memory_used,
                memory_total=memory_total,
                disk_used=disk_used,
                disk_total=disk_total,
                network_rx=network_rx,
                network_tx=network_tx
            )
        except Exception as e:
            print(f"获取资源使用情况失败: {e}")
            return ResourceUsage(
                cpu_percent=0.0,
                memory_used=0,
                memory_total=512,
                disk_used=0,
                disk_total=10240,
                network_rx=0,
                network_tx=0
            )
    
    def _parse_memory_limit(self, limit_str: str) -> int:
        """解析内存限制字符串为MB"""
        if 'GiB' in limit_str or 'GB' in limit_str:
            return int(float(limit_str.replace('GiB', '').replace('GB', '')) * 1024)
        elif 'MiB' in limit_str or 'MB' in limit_str:
            return int(float(limit_str.replace('MiB', '').replace('MB', '')))
        return 512
    
    def _parse_disk_size(self, size_str: str) -> int:
        """解析磁盘大小字符串为MB"""
        if 'GB' in size_str:
            return int(float(size_str.replace('GB', '')) * 1024)
        elif 'MB' in size_str:
            return int(float(size_str.replace('MB', '')))
        return 10240
    
    def _parse_description(self, desc: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """解析description字段
        格式: name ssh_port password nat_start nat_end
        """
        if not desc:
            return None, None, None
        
        parts = desc.split()
        if len(parts) < 3:
            return None, None, None
        
        try:
            ssh_port = int(parts[1]) if parts[1].isdigit() else None
            password = parts[2] if len(parts) > 2 else None
            nat_ports = None
            if len(parts) >= 5 and parts[3] != '0':
                nat_ports = f"{parts[3]}-{parts[4]}"
            return ssh_port, nat_ports, password
        except:
            return None, None, None
    
    def start_instance(self, name: str) -> bool:
        """启动实例"""
        try:
            container = self.client.containers.get(name)
            if container.status != 'Running':
                container.start(wait=True)
            return True
        except Exception as e:
            print(f"启动实例失败: {e}")
            return False
    
    def stop_instance(self, name: str) -> bool:
        """停止实例"""
        try:
            container = self.client.containers.get(name)
            if container.status == 'Running':
                container.stop(wait=True)
            return True
        except Exception as e:
            print(f"停止实例失败: {e}")
            return False
    
    def restart_instance(self, name: str) -> bool:
        """重启实例"""
        try:
            container = self.client.containers.get(name)
            container.restart(wait=True)
            return True
        except Exception as e:
            print(f"重启实例失败: {e}")
            return False
    
    def delete_instance(self, name: str, force: bool = False) -> bool:
        """删除实例"""
        try:
            container = self.client.containers.get(name)
            if force and container.status == 'Running':
                container.stop(wait=True)
            container.delete(wait=True)
            return True
        except Exception as e:
            print(f"删除实例失败: {e}")
            return False
    
    def get_host_info(self) -> Dict:
        """获取宿主机信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_cores": psutil.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total": memory.total // (1024 * 1024),  # MB
                "memory_used": memory.used // (1024 * 1024),
                "memory_percent": memory.percent,
                "disk_total": disk.total // (1024 * 1024 * 1024),  # GB
                "disk_used": disk.used // (1024 * 1024 * 1024),
                "disk_percent": disk.percent
            }
        except Exception as e:
            print(f"获取宿主机信息失败: {e}")
            return {}
