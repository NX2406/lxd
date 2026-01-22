#!/usr/bin/env bash
# LXD 管理面板 - 智能安装脚本（增强环境检测）
# 版本: 2.1.0
# 使用方法: bash <(curl -sL https://raw.githubusercontent.com/NX2406/lxd/main/install.sh)
set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
PLAIN='\033[0m'
INSTALL_DIR="/opt/lxd-panel"
PANEL_PORT=8000
# GitHub 仓库配置
GITHUB_USER="NX2406"
GITHUB_REPO="lxd"
GITHUB_BRANCH="main"
GITHUB_RAW="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}"
echo -e "${BLUE}======================================${PLAIN}"
echo -e "${GREEN}   LXD 管理面板 - 智能安装${PLAIN}"
echo -e "${BLUE}======================================${PLAIN}"
echo ""
# 检查 root 权限
if [ "$(id -u)" != "0" ]; then
    echo -e "${RED}错误: 必须使用 Root 权限运行${PLAIN}"
    exit 1
fi
# 检测系统
if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt-get"
    OS_TYPE="debian"
elif command -v yum >/dev/null 2>&1; then
    PKG_MANAGER="yum"
    OS_TYPE="rhel"
else
    echo -e "${RED}错误: 不支持的系统${PLAIN}"
    exit 1
fi
echo -e "${BLUE}[环境检测]${PLAIN} 开始检测系统环境..."
# ==================== 检测和安装 LXD ====================
echo -n "检测 LXD... "
if ! command -v lxc >/dev/null 2>&1; then
    echo -e "${YELLOW}未安装${PLAIN}"
    echo -e "${YELLOW}正在安装 LXD...${PLAIN}"
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt-get update -y >/dev/null 2>&1
        if command -v snap >/dev/null 2>&1; then
            snap install lxd >/dev/null 2>&1
        else
            apt-get install -y lxd >/dev/null 2>&1
        fi
    else
        yum install -y epel-release >/dev/null 2>&1
        yum install -y snapd >/dev/null 2>&1
        systemctl enable --now snapd.socket >/dev/null 2>&1
        ln -s /var/lib/snapd/snap /snap 2>/dev/null || true
        snap install lxd >/dev/null 2>&1
    fi
    
    # 初始化 LXD
    if ! lxd init --auto >/dev/null 2>&1; then
        echo -e "${YELLOW}LXD 已安装，但初始化跳过（可能已初始化）${PLAIN}"
    fi
    echo -e "${GREEN}✓ LXD 安装完成${PLAIN}"
else
    echo -e "${GREEN}✓ 已安装${PLAIN}"
    # 检查是否已初始化
    if ! lxc storage list >/dev/null 2>&1 || [ -z "$(lxc storage list --format csv 2>/dev/null)" ]; then
        echo -e "${YELLOW}初始化 LXD...${PLAIN}"
        lxd init --auto >/dev/null 2>&1
    fi
fi
# ==================== 检测和安装 Python ====================
echo -n "检测 Python 3... "
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${YELLOW}未安装${PLAIN}"
    echo -e "${YELLOW}正在安装 Python 3...${PLAIN}"
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        apt-get update -y >/dev/null 2>&1
        apt-get install -y python3 python3-pip python3-venv python3-dev >/dev/null 2>&1
    else
        yum install -y python3 python3-pip python3-devel >/dev/null 2>&1
    fi
    echo -e "${GREEN}✓ Python 3 安装完成${PLAIN}"
else
    echo -e "${GREEN}✓ 已安装${PLAIN}"
fi
# 检查 Python 版本（修复版本比较逻辑）
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
echo -n "检测 Python 版本 ($PYTHON_VERSION)... "
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}✗ 版本过低${PLAIN}"
    echo -e "${YELLOW}需要 Python 3.8+，正在尝试升级...${PLAIN}"
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt-get install -y software-properties-common >/dev/null 2>&1
        add-apt-repository -y ppa:deadsnakes/ppa >/dev/null 2>&1 || true
        apt-get update -y >/dev/null 2>&1
        apt-get install -y python3.9 python3.9-venv python3.9-pip python3.9-dev >/dev/null 2>&1
        update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 >/dev/null 2>&1
    else
        echo -e "${RED}请手动升级 Python 到 3.8 或更高版本${PLAIN}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python 已升级${PLAIN}"
else
    echo -e "${GREEN}✓ 版本符合要求${PLAIN}"
fi
# 确保安装了 venv 包（根据实际 Python 版本）
PYTHON_VERSION_FULL=$(python3 --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo $PYTHON_VERSION_FULL | cut -d. -f1)
PY_MINOR=$(echo $PYTHON_VERSION_FULL | cut -d. -f2)
PY_VER="${PY_MAJOR}.${PY_MINOR}"
echo -n "检测 Python venv... "
# 强制安装对应版本的 venv（不依赖检测）
if [ "$PKG_MANAGER" = "apt-get" ]; then
    echo -e "${YELLOW}安装中${PLAIN}"
    # 尝试安装精确版本的 venv
    if apt-get install -y python${PY_VER}-venv python${PY_VER}-dev >/dev/null 2>&1; then
        echo -e "${GREEN}✓ python${PY_VER}-venv 安装完成${PLAIN}"
    else
        # 回退到通用包
        apt-get install -y python3-venv python3-dev >/dev/null 2>&1
        echo -e "${GREEN}✓ python3-venv 安装完成${PLAIN}"
    fi
else
    yum install -y python3-devel >/dev/null 2>&1
    echo -e "${GREEN}✓ 已安装${PLAIN}"
fi
# 实际测试创建虚拟环境
echo -n "测试虚拟环境创建... "
TEST_VENV="/tmp/test_venv_$$"
if python3 -m venv "$TEST_VENV" >/dev/null 2>&1; then
    rm -rf "$TEST_VENV"
    echo -e "${GREEN}✓ 测试成功${PLAIN}"
else
    echo -e "${RED}✗ 测试失败${PLAIN}"
    echo -e "${RED}错误: 无法创建 Python 虚拟环境${PLAIN}"
    echo -e "${YELLOW}请手动运行以下命令:${PLAIN}"
    echo -e "${YELLOW}  apt update${PLAIN}"
    echo -e "${YELLOW}  apt install -y python${PY_VER}-venv${PLAIN}"
    exit 1
fi
# ==================== 安装其他依赖 ====================
echo -e "${BLUE}[1/8]${PLAIN} 安装系统依赖..."
if [ "$PKG_MANAGER" = "apt-get" ]; then
    apt-get update -y >/dev/null 2>&1
    # 安装编译依赖（bcrypt 需要）
    apt-get install -y sqlite3 curl wget build-essential libssl-dev libffi-dev \
        python3-dev gcc g++ make pkg-config >/dev/null 2>&1
else
    yum install -y sqlite curl wget gcc openssl-devel libffi-devel \
        python3-devel gcc-c++ make pkgconfig >/dev/null 2>&1
fi
echo -e "${BLUE}[2/8]${PLAIN} 创建项目目录..."
mkdir -p "$INSTALL_DIR"/{backend/app,backend/frontend/admin,data,logs}
cd "$INSTALL_DIR"
echo -e "${BLUE}[3/8]${PLAIN} 从 GitHub 下载应用文件..."
# 下载 main.py
echo -n "下载 main.py... "
if curl -sL "${GITHUB_RAW}/main.py" -o backend/app/main.py; then
    echo -e "${GREEN}✓${PLAIN}"
else
    echo -e "${RED}✗${PLAIN}"
    echo -e "${RED}错误: 无法下载 main.py${PLAIN}"
    echo -e "${YELLOW}请检查 GitHub 仓库URL: ${GITHUB_RAW}/main.py${PLAIN}"
    exit 1
fi
# 下载 index.html
echo -n "下载 index.html... "
if curl -sL "${GITHUB_RAW}/index.html" -o backend/frontend/admin/index.html; then
    echo -e "${GREEN}✓${PLAIN}"
else
    echo -e "${RED}✗${PLAIN}"
    echo -e "${RED}错误: 无法下载 index.html${PLAIN}"
    exit 1
fi
# 验证文件
if [ ! -s backend/app/main.py ] || [ ! -s backend/frontend/admin/index.html ]; then
    echo -e "${RED}错误: 下载的文件为空或不存在${PLAIN}"
    exit 1
fi
echo -e "${BLUE}[4/8]${PLAIN} 创建 Python 虚拟环境..."
cd backend
python3 -m venv venv
source venv/bin/activate
echo -e "${BLUE}[5/8]${PLAIN} 安装 Python 依赖..."
pip install --upgrade pip setuptools wheel >/dev/null 2>&1
# 先单独安装 bcrypt（确保编译成功）
echo -n "安装 bcrypt... "
if pip install bcrypt >/dev/null 2>&1; then
    echo -e "${GREEN}✓${PLAIN}"
else
    echo -e "${RED}✗ 编译失败${PLAIN}"
    echo -e "${YELLOW}尝试使用预编译版本...${PLAIN}"
    pip install --only-binary :all: bcrypt >/dev/null 2>&1 || true
fi
# 安装其他依赖
echo -n "安装其他 Python 包... "
pip install fastapi==0.109.0 uvicorn==0.27.0 sqlalchemy==2.0.25 \
    pydantic==2.5.3 pydantic-settings==2.1.0 \
    python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.6 python-telegram-bot==20.7 \
    apscheduler==3.10.4 psutil==5.9.8 aiofiles==23.2.1 >/dev/null 2>&1
echo -e "${GREEN}✓${PLAIN}"
echo ""
echo -e "${BLUE}[6/8]${PLAIN} 配置 Telegram 通知（可选）..."
read -p "是否配置 Telegram 机器人? (y/n): " setup_telegram
if [ "$setup_telegram" = "y" ]; then
    echo -e "${YELLOW}提示: 访问 @BotFather 创建机器人并获取 Token${PLAIN}"
    read -p "Bot Token: " bot_token
    read -p "Admin Chat ID: " chat_id
    
    cat > .env <<EOF
TELEGRAM_BOT_TOKEN=$bot_token
TELEGRAM_ADMIN_CHAT_ID=$chat_id
EOF
    echo -e "${GREEN}Telegram 配置完成${PLAIN}"
fi
echo -e "${BLUE}[7/8]${PLAIN} 初始化数据库..."
cd "$INSTALL_DIR/backend"
source venv/bin/activate
python3 -c "from app.main import init_db; init_db(); print('数据库初始化完成')" 2>/dev/null || echo "数据库初始化跳过（将在首次启动时自动创建）"
echo -e "${BLUE}[8/8]${PLAIN} 配置系统服务..."
cat > /etc/systemd/system/lxd-panel.service <<EOF
[Unit]
Description=LXD Management Panel
After=network.target lxd.service
Wants=lxd.service
[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
ExecStart=$INSTALL_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PANEL_PORT
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable lxd-panel
systemctl start lxd-panel
# 等待服务启动
sleep 3
# 检查服务状态
if systemctl is-active lxd-panel >/dev/null 2>&1; then
    STATUS="${GREEN}✓ 运行中${PLAIN}"
else
    STATUS="${RED}✗ 启动失败${PLAIN}"
    echo -e "${YELLOW}查看日志: journalctl -u lxd-panel -n 50${PLAIN}"
fi
SERVER_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1)
echo ""
echo -e "${GREEN}======================================${PLAIN}"
echo -e "${GREEN}   安装完成!${PLAIN}"
echo -e "${GREEN}======================================${PLAIN}"
echo ""
echo -e "服务状态: $STATUS"
echo -e "访问地址: ${BLUE}http://$SERVER_IP:$PANEL_PORT${PLAIN}"
echo ""
echo -e "管理员账号: ${YELLOW}admin${PLAIN}"
echo -e "默认密码: ${YELLOW}admin123${PLAIN}"
echo ""
echo -e "${RED}重要提示:${PLAIN}"
echo -e "  1. 请尽快登录并修改管理员密码"
echo -e "  2. 建议配置防火墙限制访问"
echo ""
echo -e "${BLUE}常用命令:${PLAIN}"
echo -e "  查看日志: ${GREEN}journalctl -u lxd-panel -f${PLAIN}"
echo -e "  重启服务: ${GREEN}systemctl restart lxd-panel${PLAIN}"
echo -e "  停止服务: ${GREEN}systemctl stop lxd-panel${PLAIN}"
echo -e "  查看状态: ${GREEN}systemctl status lxd-panel${PLAIN}"
echo ""
