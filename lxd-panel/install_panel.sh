#!/bin/bash
# LXD管理面板一键安装脚本

set -e

echo "==================================================="
echo "       LXD 管理面板一键安装脚本"
echo "==================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 检查root权限
if [ "$(id -u)" != "0" ]; then
    echo -e "${RED}错误: 必须使用 root 用户运行此脚本${NC}"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/lxd-panel"

echo -e "${YELLOW}开始安装...${NC}"

# 1. 检测操作系统
echo -e "${GREEN}[1/8] 检测操作系统...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo -e "${RED}无法检测操作系统${NC}"
    exit 1
fi

echo "检测到系统: $OS $VER"

# 2. 安装系统依赖
echo -e "${GREEN}[2/8] 安装系统依赖...${NC}"
if command -v apt-get > /dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv nginx lxd jq bc curl > /dev/null 2>&1
elif command -v yum > /dev/null 2>&1; then
    yum install -y python3 python3-pip nginx lxd jq bc curl > /dev/null 2>&1
else
    echo -e "${RED}不支持的包管理器${NC}"
    exit 1
fi

# 3. 检查LXD环境
echo -e "${GREEN}[3/8] 检查LXD环境...${NC}"
if ! command -v lxc > /dev/null 2>&1; then
    echo -e "${RED}LXD未安装或未正确配置${NC}"
    exit 1
fi

if ! lxc storage list > /dev/null 2>&1 || [ -z "$(lxc storage list --format csv)" ]; then
    echo "初始化LXD..."
    lxd init --auto
fi

# 4. 创建安装目录
echo -e "${GREEN}[4/8] 创建安装目录...${NC}"
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/backend" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/frontend" "$INSTALL_DIR/"

# 5. 安装Python依赖
echo -e "${GREEN}[5/8] 安装Python依赖...${NC}"
cd "$INSTALL_DIR/backend"

# 创建虚拟环境(可选,这里直接全局安装)
pip3 install -r requirements.txt > /dev/null 2>&1

# 6. 配置systemd服务
echo -e "${GREEN}[6/8] 配置systemd服务...${NC}"
cp "$SCRIPT_DIR/systemd/lxd-panel.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable lxd-panel.service
systemctl start lxd-panel.service

# 等待服务启动
echo "等待后端服务启动..."
sleep 5

# 检查服务状态
if systemctl is-active --quiet lxd-panel.service; then
    echo -e "${GREEN}后端服务启动成功${NC}"
else
    echo -e "${RED}后端服务启动失败,请查看日志: journalctl -u lxd-panel -n 50${NC}"
    exit 1
fi

# 7. 配置Nginx
echo -e "${GREEN}[7/8] 配置Nginx...${NC}"
cp "$SCRIPT_DIR/nginx/lxd-panel.conf" /etc/nginx/sites-available/lxd-panel.conf

# 创建软链接(Debian/Ubuntu)
if [ -d /etc/nginx/sites-enabled ]; then
    ln -sf /etc/nginx/sites-available/lxd-panel.conf /etc/nginx/sites-enabled/
else
    # CentOS/RHEL
    if ! grep -q "include /etc/nginx/sites-available/lxd-panel.conf" /etc/nginx/nginx.conf; then
        sed -i '/include \/etc\/nginx\/conf.d\/\*.conf;/a\    include /etc/nginx/sites-available/lxd-panel.conf;' /etc/nginx/nginx.conf
    fi
fi

# 测试Nginx配置
nginx -t > /dev/null 2>&1
if [ $? -eq 0 ]; then
    systemctl restart nginx
    echo -e "${GREEN}Nginx配置成功${NC}"
else
    echo -e "${RED}Nginx配置错误${NC}"
    exit 1
fi

# 8. 完成安装
echo -e "${GREEN}[8/8] 完成安装${NC}"

# 获取服务器IP
SERVER_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1 | head -n 1)

echo ""
echo "==================================================="
echo -e "${GREEN}安装完成!${NC}"
echo "==================================================="
echo ""
echo -e "访问地址: ${GREEN}http://$SERVER_IP${NC}"
echo -e "默认用户名: ${YELLOW}admin${NC}"
echo -e "默认密码: ${YELLOW}admin${NC}"
echo ""
echo -e "${YELLOW}重要提示:${NC}"
echo "1. 请立即修改默认密码"
echo "2. 建议配置HTTPS证书以提高安全性"
echo "3. 查看后端日志: journalctl -u lxd-panel -f"
echo "4. 查看Nginx日志: tail -f /var/log/nginx/access.log"
echo ""
echo "==================================================="
echo ""
