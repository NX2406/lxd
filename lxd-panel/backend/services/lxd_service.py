"""LXD操作服务"""
import pylxd
from typing import List, Dict, Optional
import subprocess
import re

class LXDService:
    def __init__(self):
        """初始化LXD客户端"""
        try:
            self.client = pylxd.Client()
        except Exception as e:
            raise Exception(f"无法连接到LXD: {str(e)}")
    
    def get_all_containers(self) -> List[Dict]:
        """获取所有容器列表"""
        containers = []
        for container in self.client.containers.all():
            info = self._get_container_info(container)
            containers.append(info)
        return containers
    
    def get_container(self, name: str) -> Optional[Dict]:
        """获取单个容器信息"""
        try:
            container = self.client.containers.get(name)
            return self._get_container_info(container)
        except pylxd.exceptions.NotFound:
            return None
    
    def _get_container_info(self, container) -> Dict:
        """提取容器信息"""
        # 从description中解析信息
        desc = container.config.get('user.description', '')
        parts = desc.split()
        
        ssh_port = parts[1] if len(parts) > 1 else None
        password = parts[2] if len(parts) > 2 else None
        nat_start = int(parts[3]) if len(parts) > 3 and parts[3] != '0' else None
        nat_end = int(parts[4]) if len(parts) > 4 and parts[4] != '0' else None
        
        # 获取IP地址
        ip_address = None
        if container.state().network:
            eth0 = container.state().network.get('eth0', {})
            for addr in eth0.get('addresses', []):
                if addr['family'] == 'inet':
                    ip_address = addr['address']
                    break
        
        # 获取资源配置
        cpu_limit = container.config.get('limits.cpu', '1')
        memory_limit = container.config.get('limits.memory', '512MiB')
        
        # 解析内存值
        memory_mb = self._parse_memory(memory_limit)
        
        return {
            'name': container.name,
            'status': container.status,
            'ip_address': ip_address,
            'cpu': cpu_limit,
            'memory': memory_mb,
            'ssh_port': ssh_port,
            'password': password,
            'nat_start': nat_start,
            'nat_end': nat_end,
            'architecture': container.architecture,
            'created_at': container.created_at
        }
    
    def _parse_memory(self, memory_str: str) -> int:
        """解析内存字符串为MB"""
        if 'GiB' in memory_str or 'GB' in memory_str:
            return int(float(re.findall(r'[\d.]+', memory_str)[0]) * 1024)
        elif 'MiB' in memory_str or 'MB' in memory_str:
            return int(float(re.findall(r'[\d.]+', memory_str)[0]))
        return 512  # 默认值
    
    def start_container(self, name: str) -> bool:
        """启动容器"""
        try:
            container = self.client.containers.get(name)
            if container.status != 'Running':
                container.start(wait=True)
            return True
        except Exception as e:
            raise Exception(f"启动容器失败: {str(e)}")
    
    def stop_container(self, name: str) -> bool:
        """停止容器"""
        try:
            container = self.client.containers.get(name)
            if container.status == 'Running':
                container.stop(wait=True)
            return True
        except Exception as e:
            raise Exception(f"停止容器失败: {str(e)}")
    
    def restart_container(self, name: str) -> bool:
        """重启容器"""
        try:
            container = self.client.containers.get(name)
            container.restart(wait=True)
            return True
        except Exception as e:
            raise Exception(f"重启容器失败: {str(e)}")
    
    def delete_container(self, name: str) -> bool:
        """删除容器"""
        try:
            container = self.client.containers.get(name)
            if container.status == 'Running':
                container.stop(wait=True)
            container.delete(wait=True)
            return True
        except Exception as e:
            raise Exception(f"删除容器失败: {str(e)}")
    
    def create_container(self, config: Dict) -> Dict:
        """
        创建容器
        使用原有脚本的逻辑通过subprocess调用
        """
        # 这里我们将调用原有的bash脚本来创建容器
        # 保持与原有脚本的兼容性
        raise NotImplementedError("容器创建将通过bash脚本实现")
    
    def rebuild_container(self, name: str, os_type: str, os_version: str) -> bool:
        """
        重装容器系统
        使用lxc rebuild命令
        """
        try:
            container = self.client.containers.get(name)
            
            # 停止容器
            if container.status == 'Running':
                container.stop(wait=True)
            
            # 构建镜像别名
            image_alias = f"{os_type}/{os_version}" if os_version else os_type
            
            # 使用subprocess调用lxc rebuild
            # pylxd不直接支持rebuild,需要用命令行
            cmd = ['lxc', 'rebuild', name, f'images:{image_alias}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"重装失败: {result.stderr}")
            
            return True
        except Exception as e:
            raise Exception(f"重装容器失败: {str(e)}")
    
    def get_container_stats(self, name: str) -> Optional[Dict]:
        """获取容器实时统计信息"""
        try:
            container = self.client.containers.get(name)
            if container.status != 'Running':
                return None
            
            state = container.state()
            
            # CPU使用率
            cpu_usage = 0
            if hasattr(state, 'cpu') and state.cpu:
                cpu_usage = state.cpu.usage / 1000000000  # 转换为秒
            
            # 内存使用
            memory_usage = 0
            memory_total = 0
            if hasattr(state, 'memory') and state.memory:
                memory_usage = state.memory.usage / (1024 * 1024)  # 转换为MB
                memory_total = state.memory.usage_peak / (1024 * 1024) if hasattr(state.memory, 'usage_peak') else memory_usage
            
            # 网络统计
            network_rx = 0
            network_tx = 0
            if state.network:
                eth0 = state.network.get('eth0', {})
                if 'counters' in eth0:
                    network_rx = eth0['counters'].get('bytes_received', 0)
                    network_tx = eth0['counters'].get('bytes_sent', 0)
            
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'memory_total': memory_total,
                'network_rx': network_rx,
                'network_tx': network_tx
            }
        except Exception as e:
            print(f"获取容器统计失败: {str(e)}")
            return None

# 全局LXD服务实例
lxd_service = LXDService()
