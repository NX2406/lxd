"""容器创建服务 - 直接使用LXD API"""
import pylxd
import secrets
import string
import time
from typing import Dict

class ContainerCreator:
    def __init__(self):
        self.client = pylxd.Client()
    
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
        创建并配置容器
        """
        try:
            password = self.generate_password()
            
            # 1. 创建容器配置
            config = {
                'name': name,
                'source': {
                    'type': 'image',
                    'mode': 'pull',
                    'server': 'https://images.linuxcontainers.org',
                    'protocol': 'simplestreams',
                    'alias': f'{os_type}/{os_version}'
                },
                'config': {
                    'limits.cpu': str(cpu),
                    'limits.memory': f'{memory}MB',
                    'user.user-data': self._get_cloud_init_config(password, ssh_port)
                },
                'devices': {
                    'root': {
                        'path': '/',
                        'pool': 'default',
                        'type': 'disk',
                        'size': f'{disk}GB'
                    },
                    'eth0': {
                        'name': 'eth0',
                        'nictype': 'bridged',
                        'parent': 'lxdbr0',
                        'type': 'nic'
                    }
                }
            }
            
            # 添加带宽限制
            if bandwidth > 0:
                config['devices']['eth0']['limits.ingress'] = f'{bandwidth}Mbit'
                config['devices']['eth0']['limits.egress'] = f'{bandwidth}Mbit'
            
            # 2. 创建容器
            print(f"正在创建容器 {name}...")
            container = self.client.containers.create(config, wait=True)
            
            # 3. 启动容器
            print(f"正在启动容器 {name}...")
            container.start(wait=True)
            
            # 4. 等待网络就绪
            time.sleep(5)
            
            # 5. 获取IP地址
            container.sync()
            ip_address = self._get_container_ip(container)
            
            # 6. 配置SSH端口转发（如果需要）
            if ssh_port and ssh_port != 22:
                self._setup_ssh_port_forward(name, ssh_port, ip_address)
            
            # 7. 配置NAT端口转发（如果需要）
            if nat_start > 0 and nat_end > 0:
                self._setup_nat_forwards(name, nat_start, nat_end, ip_address)
            
            return {
                'success': True,
                'message': f'容器 {name} 创建成功',
                'data': {
                    'name': name,
                    'ip': ip_address,
                    'password': password,
                    'ssh_port': ssh_port,
                    'status': 'Running'
                }
            }
            
        except pylxd.exceptions.LXDAPIException as e:
            return {
                'success': False,
                'message': f'LXD API错误: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'创建失败: {str(e)}'
            }
    
    def _get_cloud_init_config(self, password: str, ssh_port: int = 22) -> str:
        """生成cloud-init配置"""
        return f"""#cloud-config
users:
  - name: root
    lock_passwd: false
    plain_text_passwd: {password}
    
ssh_pwauth: true
disable_root: false

packages:
  - openssh-server
  - curl
  - wget
  - vim

runcmd:
  - sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
  - sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
  - systemctl restart sshd || systemctl restart ssh
  - echo "Container initialized" > /var/log/init-complete
"""
    
    def _get_container_ip(self, container) -> str:
        """获取容器IP地址"""
        try:
            state = container.state()
            network = state.network
            if network and 'eth0' in network:
                addresses = network['eth0']['addresses']
                for addr in addresses:
                    if addr['family'] == 'inet' and addr['address'] != '127.0.0.1':
                        return addr['address']
            return None
        except:
            return None
    
    def _setup_ssh_port_forward(self, container_name: str, host_port: int, container_ip: str):
        """设置SSH端口转发"""
        try:
            import subprocess
            # 使用iptables设置端口转发
            cmd = f"iptables -t nat -A PREROUTING -p tcp --dport {host_port} -j DNAT --to-destination {container_ip}:22"
            subprocess.run(cmd, shell=True, check=True)
            print(f"SSH端口转发设置成功: {host_port} -> {container_ip}:22")
        except Exception as e:
            print(f"设置SSH端口转发失败: {str(e)}")
    
    def _setup_nat_forwards(self, container_name: str, start_port: int, end_port: int, container_ip: str):
        """设置NAT端口转发范围"""
        try:
            import subprocess
            for port in range(start_port, end_port + 1):
                cmd = f"iptables -t nat -A PREROUTING -p tcp --dport {port} -j DNAT --to-destination {container_ip}:{port}"
                subprocess.run(cmd, shell=True, check=True)
            print(f"NAT端口转发设置成功: {start_port}-{end_port} -> {container_ip}")
        except Exception as e:
            print(f"设置NAT端口转发失败: {str(e)}")

# 全局实例
container_creator = ContainerCreator()
