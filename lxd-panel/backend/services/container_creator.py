"""容器创建服务 - 调用bash脚本"""
import subprocess
import re
import secrets
import string
from typing import Dict, Optional

class ContainerCreationService:
    def __init__(self, script_path: str = "/root/panel.txt"):
        """
        初始化容器创建服务
        :param script_path: bash脚本路径
        """
        self.script_path = script_path
    
    def generate_password(self, length: int = 12) -> str:
        """生成随机密码"""
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def create_container(
        self,
        name: str,
        cpu: float,
        memory: int,
        disk: int,
        os_type: str,
        os_version: str,
        ssh_port: int,
        nat_start: int = 0,
        nat_end: int = 0,
        bandwidth: int = 10
    ) -> Dict:
        """
        创建容器
        :return: 创建结果字典
        """
        try:
            # 生成随机密码
            password = self.generate_password()
            
            # 构建expect脚本来自动化输入
            expect_script = f'''#!/usr/bin/expect -f
set timeout 300

spawn bash {self.script_path}

# 选择创建实例
expect "请选择功能"
send "1\\r"

# 容器名称
expect "请输入容器名称"
send "{name}\\r"

# CPU核数
expect "请输入CPU核数"
send "{cpu}\\r"

# 内存大小
expect "请输入内存大小"
send "{memory}\\r"

# 硬盘大小
expect "输入磁盘大小"
send "{disk}\\r"

# 操作系统镜像
expect "请选择操作系统镜像"
send "{os_type}:{os_version}\\r"

# SSH端口
expect "请输入SSH端口"
send "{ssh_port}\\r"

# 密码
expect "请输入root密码"
send "{password}\\r"

# 确认密码
expect "请再次输入密码"
send "{password}\\r"

# NAT端口范围
expect "请输入NAT端口起始"
send "{nat_start}\\r"

expect "请输入NAT端口结束"
send "{nat_end}\\r"

# 带宽限制
expect "请输入带宽限制"
send "{bandwidth}\\r"

# 等待创建完成
expect {{
    "创建成功" {{
        send_user "\\nSUCCESS\\n"
    }}
    "创建失败" {{
        send_user "\\nFAILED\\n"
    }}
    timeout {{
        send_user "\\nTIMEOUT\\n"
    }}
}}

expect eof
'''
            
            # 写入临时expect脚本
            expect_file = f"/tmp/create_container_{name}.exp"
            with open(expect_file, 'w') as f:
                f.write(expect_script)
            
            # 给予执行权限
            subprocess.run(['chmod', '+x', expect_file], check=True)
            
            # 执行expect脚本
            result = subprocess.run(
                [expect_file],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            # 清理临时文件
            subprocess.run(['rm', '-f', expect_file])
            
            # 检查结果
            if 'SUCCESS' in result.stdout:
                return {
                    'success': True,
                    'message': f'容器 {name} 创建成功',
                    'data': {
                        'name': name,
                        'password': password,
                        'ssh_port': ssh_port,
                        'ip': self._get_container_ip(name)
                    }
                }
            else:
                error_msg = self._extract_error(result.stdout + result.stderr)
                return {
                    'success': False,
                    'message': f'容器创建失败: {error_msg}'
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': '容器创建超时(超过10分钟)'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'容器创建异常: {str(e)}'
            }
    
    def _get_container_ip(self, name: str) -> Optional[str]:
        """获取容器IP地址"""
        try:
            result = subprocess.run(
                ['lxc', 'list', name, '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                if data and len(data) > 0:
                    state = data[0].get('state', {})
                    network = state.get('network', {})
                    for iface, details in network.items():
                        if iface != 'lo':
                            addresses = details.get('addresses', [])
                            for addr in addresses:
                                if addr.get('family') == 'inet':
                                    return addr.get('address')
            return None
        except:
            return None
    
    def _extract_error(self, output: str) -> str:
        """从输出中提取错误信息"""
        # 尝试提取有用的错误信息
        lines = output.split('\n')
        for line in lines:
            if 'error' in line.lower() or '失败' in line or 'failed' in line.lower():
                return line.strip()
        return '未知错误'

# 全局实例
container_creator = ContainerCreationService()
