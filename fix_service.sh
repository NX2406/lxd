#!/usr/bin/env bash
# LXD 管理面板 - 服务修复脚本
# 用于修复已安装但无法启动的服务

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
PLAIN='\033[0m'

echo -e "${BLUE}======================================${PLAIN}"
echo -e "${GREEN}   LXD 管理面板 - 服务修复${PLAIN}"
echo -e "${BLUE}======================================${PLAIN}"
echo ""

if [ "$(id -u)" != "0" ]; then
    echo -e "${RED}错误: 需要 Root 权限${PLAIN}"
    exit 1
fi

INSTALL_DIR="/opt/lxd-panel"

echo -e "${BLUE}[1/6]${PLAIN} 检查日志..."
echo "最近的错误:"
journalctl -u lxd-panel -n 20 --no-pager | grep -i error || echo "无明显错误"
echo ""

echo -e "${BLUE}[2/6]${PLAIN} 检查文件..."
if [ ! -f "$INSTALL_DIR/backend/app/main.py" ]; then
    echo -e "${RED}✗ main.py 不存在${PLAIN}"
    exit 1
fi
echo -e "${GREEN}✓ 文件检查通过${PLAIN}"

echo -e "${BLUE}[3/6]${PLAIN} 安装编译依赖..."
apt-get update -y >/dev/null 2>&1
apt-get install -y build-essential python3-dev libssl-dev libffi-dev \
    gcc g++ make pkg-config >/dev/null 2>&1
echo -e "${GREEN}✓ 依赖安装完成${PLAIN}"

echo -e "${BLUE}[4/6]${PLAIN} 重装 Python 包..."
cd "$INSTALL_DIR/backend"
source venv/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel >/dev/null 2>&1

# 重装所有包
pip uninstall -y bcrypt passlib >/dev/null 2>&1
pip install bcrypt passlib[bcrypt] >/dev/null 2>&1

pip install --force-reinstall fastapi uvicorn sqlalchemy pydantic \
    pydantic-settings python-jose passlib python-multipart \
    python-telegram-bot apscheduler psutil aiofiles >/dev/null 2>&1

echo -e "${GREEN}✓ Python 包重装完成${PLAIN}"

echo -e "${BLUE}[5/6]${PLAIN} 测试启动..."
timeout 5 python3 -c "from app.main import app; print('✓ 导入成功')" 2>&1 | grep -q "✓ 导入成功"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 应用可以导入${PLAIN}"
else
    echo -e "${RED}✗ 应用导入失败${PLAIN}"
    echo "详细错误:"
    python3 -c "from app.main import app"
    exit 1
fi

echo -e "${BLUE}[6/6]${PLAIN} 重启服务..."
systemctl restart lxd-panel
sleep 3

if systemctl is-active lxd-panel >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 服务启动成功！${PLAIN}"
    
    SERVER_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1)
    echo ""
    echo -e "${GREEN}======================================${PLAIN}"
    echo -e "访问地址: ${BLUE}http://$SERVER_IP:8000${PLAIN}"
    echo -e "用户名: ${YELLOW}admin${PLAIN}"
    echo -e "密码: ${YELLOW}admin123${PLAIN}"
    echo -e "${GREEN}======================================${PLAIN}"
else
    echo -e "${RED}✗ 服务仍然无法启动${PLAIN}"
    echo ""
    echo "查看完整日志:"
    journalctl -u lxd-panel -n 50 --no-pager
fi
