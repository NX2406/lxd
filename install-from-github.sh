#!/bin/bash
#
# LXD管理面板 - GitHub一键安装脚本
# 从GitHub仓库下载并安装
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

# GitHub仓库配置（需要替换为您的实际仓库地址）
GITHUB_USER="YOUR_USERNAME"  # 修改为您的GitHub用户名
GITHUB_REPO="lxd-panel"      # 修改为您的仓库名
GITHUB_BRANCH="main"         # 分支名，可能是main或master

# 或者使用完整URL
# GITHUB_URL="https://github.com/YOUR_USERNAME/lxd-panel"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查root权限
check_root() {
    if [ "$(id -u)" != "0" ]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检测系统
detect_system() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        log_error "无法检测系统类型"
        exit 1
    fi
    log_info "检测到系统: $OS $VERSION"
}

# 安装基础依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        apt-get update -qq
        apt-get install -y python3 python3-pip python3-venv nginx curl wget git unzip
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip nginx curl wget git unzip
    else
        log_error "不支持的包管理器"
        exit 1
    fi
    
    log_success "系统依赖安装完成"
}

# 下载代码
download_from_github() {
    log_info "从GitHub下载代码..."
    
    TEMP_DIR="/tmp/lxd-panel-install"
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # 方式1: 使用git clone（推荐）
    if command -v git &> /dev/null; then
        log_info "使用git下载..."
        git clone -b "$GITHUB_BRANCH" "https://github.com/${GITHUB_USER}/${GITHUB_REPO}.git" .
    else
        # 方式2: 下载ZIP
        log_info "使用wget下载ZIP..."
        wget "https://github.com/${GITHUB_USER}/${GITHUB_REPO}/archive/refs/heads/${GITHUB_BRANCH}.zip" -O repo.zip
        unzip -q repo.zip
        mv ${GITHUB_REPO}-${GITHUB_BRANCH}/* .
        rm repo.zip
    fi
    
    log_success "代码下载完成"
}

# 创建安装目录
create_directories() {
    log_info "创建安装目录..."
    
    INSTALL_DIR="/opt/lxd-panel"
    mkdir -p "$INSTALL_DIR"/{backend,frontend,logs}
    
    log_success "目录创建完成: $INSTALL_DIR"
}

# 复制文件
copy_files() {
    log_info "复制面板文件..."
    
    TEMP_DIR="/tmp/lxd-panel-install"
    
    # 复制后端文件
    if [ -d "$TEMP_DIR/lxd-panel/backend" ]; then
        cp -r "$TEMP_DIR/lxd-panel/backend"/* "$INSTALL_DIR/backend/"
    else
        log_error "后端文件不存在"
        exit 1
    fi
    
    # 复制前端文件
    if [ -d "$TEMP_DIR/lxd-panel/frontend" ]; then
        cp -r "$TEMP_DIR/lxd-panel/frontend"/* "$INSTALL_DIR/frontend/"
    else
        log_error "前端文件不存在"
        exit 1
    fi
    
    log_success "文件复制完成"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    cd "$INSTALL_DIR/backend"
    
    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip -q
    
    # 安装依赖
    pip install -r requirements.txt -q
    
    deactivate
    
    log_success "Python依赖安装完成"
}

# 生成API密钥
generate_api_key() {
    log_info "生成API密钥..."
    
    API_KEY=$(openssl rand -hex 32)
    echo "$API_KEY" > "$INSTALL_DIR/api_key.txt"
    chmod 600 "$INSTALL_DIR/api_key.txt"
    
    log_success "API密钥已生成"
}

# 配置systemd服务
setup_systemd() {
    log_info "配置systemd服务..."
    
    cat > /etc/systemd/system/lxd-panel.service << EOF
[Unit]
Description=LXD管理面板后端服务
After=network.target lxd.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
ExecStart=$INSTALL_DIR/backend/venv/bin/python app.py
Restart=always
RestartSec=5
StandardOutput=append:$INSTALL_DIR/logs/backend.log
StandardError=append:$INSTALL_DIR/logs/backend-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable lxd-panel
    
    log_success "systemd服务配置完成"
}

# 配置Nginx
setup_nginx() {
    log_info "配置Nginx..."
    
    cat > /etc/nginx/sites-available/lxd-panel << 'EOF'
server {
    listen 8080;
    server_name _;
    
    root /opt/lxd-panel/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/lxd-panel /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    systemctl enable nginx
    
    log_success "Nginx配置完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 8080/tcp comment 'LXD Panel'
        log_success "UFW防火墙规则已添加"
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=8080/tcp
        firewall-cmd --reload
        log_success "FirewallD防火墙规则已添加"
    else
        log_info "未检测到防火墙，请手动开放8080端口"
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    systemctl start lxd-panel
    sleep 2
    
    if systemctl is-active --quiet lxd-panel; then
        log_success "LXD管理面板后端服务已启动"
    else
        log_error "后端服务启动失败，请检查日志"
        journalctl -u lxd-panel -n 20
        exit 1
    fi
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    rm -rf /tmp/lxd-panel-install
    log_success "清理完成"
}

# 显示安装信息
show_info() {
    SERVER_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1 | head -n1)
    
    echo ""
    echo "========================================="
    log_success "LXD管理面板安装完成！"
    echo "========================================="
    echo ""
    echo -e "${GREEN}访问地址:${NC}"
    echo "  http://$SERVER_IP:8080"
    echo ""
    echo -e "${GREEN}服务管理:${NC}"
    echo "  启动: systemctl start lxd-panel"
    echo "  停止: systemctl stop lxd-panel"
    echo "  重启: systemctl restart lxd-panel"
    echo "  状态: systemctl status lxd-panel"
    echo ""
    echo -e "${GREEN}日志位置:${NC}"
    echo "  $INSTALL_DIR/logs/backend.log"
    echo ""
    echo "========================================="
}

# 主函数
main() {
    echo "========================================="
    echo "    LXD管理面板 - GitHub一键安装"
    echo "========================================="
    echo ""
    
    check_root
    detect_system
    install_dependencies
    download_from_github
    create_directories
    copy_files
    install_python_deps
    generate_api_key
    setup_systemd
    setup_nginx
    setup_firewall
    start_services
    cleanup
    show_info
    
    log_success "安装流程全部完成！"
}

main "$@"
