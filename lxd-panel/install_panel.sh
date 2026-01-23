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
    echo "更新软件包列表..."
    apt-get update -qq || true
    echo "安装依赖包: python3 python3-pip python3-venv nginx jq bc curl..."
    apt-get install -y python3 python3-pip python3-venv nginx jq bc curl
    
    # LXD单独安装，如果失败也继续
    if ! command -v lxc > /dev/null 2>&1; then
        echo "尝试安装LXD..."
        apt-get install -y lxd || snap install lxd || echo "LXD需要手动安装"
    fi
elif command -v yum > /dev/null 2>&1; then
    echo "安装依赖包..."
    yum install -y python3 python3-pip nginx jq bc curl
    
    # LXD单独处理
    if ! command -v lxc > /dev/null 2>&1; then
        echo "尝试安装LXD..."
        yum install -y epel-release || true
        yum install -y lxd || snap install lxd || echo "LXD需要手动安装"
    fi
else
    echo -e "${RED}不支持的包管理器${NC}"
    exit 1
fi

echo -e "${GREEN}系统依赖安装完成${NC}"

# 验证Python安装
echo "验证Python环境..."
if ! command -v python3 > /dev/null 2>&1; then
    echo -e "${RED}Python3安装失败${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $PYTHON_VERSION"

# 确保pip是最新的
echo "更新pip..."
python3 -m pip install --upgrade pip --quiet || true

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
echo -e "${GREEN}[4/8] 准备安装目录...${NC}"
# 如果通过quick_install.sh调用，文件已经在正确位置
if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
    echo "复制文件到 $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    cp -r "$SCRIPT_DIR/backend" "$INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/frontend" "$INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/systemd" "$INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/nginx" "$INSTALL_DIR/" 2>/dev/null || true
else
    echo "文件已在安装目录，跳过复制..."
fi

# 5. 安装Python依赖
echo -e "${GREEN}[5/8] 安装Python依赖...${NC}"
cd "$INSTALL_DIR/backend"

# 显示安装过程，方便调试
echo "安装Python包..."
pip3 install -r requirements.txt --quiet || {
    echo -e "${YELLOW}尝试使用清华源重新安装...${NC}"
    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
}

# 6. 配置systemd服务
echo -e "${GREEN}[6/8] 配置systemd服务...${NC}"
# 查找service文件
if [ -f "$SCRIPT_DIR/systemd/lxd-panel.service" ]; then
    cp "$SCRIPT_DIR/systemd/lxd-panel.service" /etc/systemd/system/
elif [ -f "$INSTALL_DIR/systemd/lxd-panel.service" ]; then
    cp "$INSTALL_DIR/systemd/lxd-panel.service" /etc/systemd/system/
else
    echo -e "${RED}找不到systemd服务文件${NC}"
    exit 1
fi
systemctl daemon-reload
systemctl enable lxd-panel.service

echo "启动后端服务..."
systemctl start lxd-panel.service

# 等待服务启动
echo "等待后端服务启动..."
sleep 3

# 检查服务状态
if systemctl is-active --quiet lxd-panel.service; then
    echo -e "${GREEN}后端服务启动成功${NC}"
    # 测试API
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}API健康检查通过${NC}"
    else
        echo -e "${YELLOW}警告: API可能还在启动中...${NC}"
    fi
else
    echo -e "${RED}后端服务启动失败${NC}"
    echo "查看日志: journalctl -u lxd-panel -n 50"
    journalctl -u lxd-panel -n 20 --no-pager
    exit 1
fi

# 7. 配置Nginx
echo -e "${GREEN}[7/8] 配置Nginx...${NC}"
# 查找nginx配置文件
if [ -f "$SCRIPT_DIR/nginx/lxd-panel.conf" ]; then
    cp "$SCRIPT_DIR/nginx/lxd-panel.conf" /etc/nginx/sites-available/lxd-panel.conf
elif [ -f "$INSTALL_DIR/nginx/lxd-panel.conf" ]; then
    cp "$INSTALL_DIR/nginx/lxd-panel.conf" /etc/nginx/sites-available/lxd-panel.conf
else
    echo -e "${RED}找不到nginx配置文件${NC}"
    exit 1
fi

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
echo "测试Nginx配置..."
if nginx -t 2>&1; then
    systemctl restart nginx
    echo -e "${GREEN}Nginx配置成功${NC}"
else
    echo -e "${RED}Nginx配置错误，但继续安装...${NC}"
    echo -e "${YELLOW}请手动检查配置: nginx -t${NC}"
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
