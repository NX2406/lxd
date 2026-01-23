#!/bin/bash
# LXD管理面板 - GitHub一键部署脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/你的用户名/仓库名/main/quick_install.sh | bash

set -e

echo "==================================================="
echo "       LXD 管理面板 - 一键部署"
echo "==================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 检查root权限
if [ "$(id -u)" != "0" ]; then
    echo -e "${RED}错误: 必须使用 root 用户运行此脚本${NC}"
    exit 1
fi

# GitHub仓库地址
GITHUB_REPO="https://github.com/NX2406/lxd.git"
INSTALL_DIR="/opt/lxd-panel"
REPO_SUBDIR="lxd-panel"  # 仓库中的子目录

echo -e "${GREEN}[1/3] 克隆GitHub仓库...${NC}"
# 安装git
if ! command -v git > /dev/null 2>&1; then
    if command -v apt-get > /dev/null 2>&1; then
        apt-get update -qq && apt-get install -y git
    elif command -v yum > /dev/null 2>&1; then
        yum install -y git
    fi
fi

# 克隆仓库
if [ -d "$INSTALL_DIR" ]; then
    echo "目录已存在，删除旧版本..."
    rm -rf "$INSTALL_DIR"
fi

# 克隆到临时目录
TEMP_DIR="/tmp/lxd-panel-install-$$"
git clone "$GITHUB_REPO" "$TEMP_DIR"

# 复制子目录到安装目录
if [ -d "$TEMP_DIR/$REPO_SUBDIR" ]; then
    mv "$TEMP_DIR/$REPO_SUBDIR" "$INSTALL_DIR"
else
    # 如果没有子目录，直接使用根目录
    mv "$TEMP_DIR" "$INSTALL_DIR"
fi

# 清理临时目录
rm -rf "$TEMP_DIR"

echo -e "${GREEN}[2/3] 进入项目目录...${NC}"
cd "$INSTALL_DIR"

echo -e "${GREEN}[3/3] 执行安装脚本...${NC}"
chmod +x install_panel.sh
./install_panel.sh

echo -e "${GREEN}部署完成!${NC}"
