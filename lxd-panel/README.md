# LXD 管理面板

一个现代化的 LXD 容器管理面板,提供直观的 Web 界面来管理 LXD 容器实例。

## 功能特性

✨ **容器管理**
- 创建、启动、停止、重启、删除容器
- 重装容器系统
- 查看容器详细信息(IP、SSH端口、密码等)

📊 **实时监控**
- CPU 使用率
- 内存使用情况
- 网络流量(接收/发送)
- 磁盘使用率
- 负载信息
- **24小时历史数据存储**

🎨 **现代化界面**
- 深色主题设计
- 紫蓝渐变配色
- 响应式布局
- 实时数据更新

🔐 **安全特性**
- JWT Token 认证
- API 请求验证
- 密码加密存储

🖥️ **VNC 支持**
- 远程控制台访问(需在容器中安装 VNC 服务器)

## 技术栈

### 后端
- **FastAPI** - 高性能异步 Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **pylxd** - LXD Python 客户端
- **SQLite** - 轻量级数据库
- **WebSocket** - 实时数据推送

### 前端
- **原生 HTML/CSS/JavaScript** - 无需编译
- **Chart.js** - 数据可视化
- **响应式设计** - 适配各种设备

### 部署
- **Nginx** - 反向代理和静态文件服务
- **systemd** - 服务管理
- **一键安装脚本** - 快速部署

## 安装步骤

### 前提条件

- Ubuntu 20.04+ / Debian 11+ / CentOS 7+
- Root 权限
- 已安装并配置 LXD

### 🚀 方法1: GitHub一键部署（推荐）

在Linux服务器上执行以下命令：

```bash
curl -fsSL https://raw.githubusercontent.com/NX2406/lxd/main/quick_install.sh | bash
```

或使用wget：

```bash
wget -qO- https://raw.githubusercontent.com/NX2406/lxd/main/quick_install.sh | bash
```

### 方法2: 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/NX2406/lxd.git
cd lxd

# 2. 运行安装脚本
chmod +x install_panel.sh
./install_panel.sh
```

安装完成后,访问 `http://服务器IP` 即可使用。

### 默认账号

- 用户名: `admin`
- 密码: `admin`

**⚠️ 请立即修改默认密码!**

## 使用指南

### 创建容器

1. 点击右上角"创建容器"按钮
2. 填写容器配置:
   - 名称:仅允许字母、数字、连字符
   - CPU: 核心数(支持小数,如 0.5)
   - 内存: MB 为单位
   - 硬盘: GB 为单位
   - 操作系统: 选择预置镜像
   - SSH 端口: 1024-65535
3. 点击"创建"

### 容器操作

- **启动**: 点击容器卡片上的"启动"按钮
- **停止**: 点击"停止"按钮
- **重启**: 点击"重启"按钮
- **删除**: 点击"删除"按钮(不可恢复!)
- **查看详情**: 点击容器卡片

### 监控数据

点击容器卡片查看详情,可见:
- 实时资源使用情况
- 过去24小时的历史数据图表
- 自动每5秒更新一次

### VNC 控制台

1. 在容器中安装 VNC 服务器:
   ```bash
   # Debian/Ubuntu
   apt-get install x11vnc
   
   # CentOS/RHEL
   yum install tigervnc-server
   ```

2. 启动 VNC 服务:
   ```bash
   x11vnc -display :0 -forever
   ```

3. 在面板中点击"VNC"按钮访问

## 配置

### 修改默认端口

后端端口(默认 8000):
```bash
# 编辑 systemd 服务文件
vim /etc/systemd/system/lxd-panel.service

# 修改 ExecStart 行的 --port 参数
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 重启服务
systemctl daemon-reload
systemctl restart lxd-panel
```

前端端口(默认 80):
```bash
# 编辑 Nginx 配置
vim /etc/nginx/sites-available/lxd-panel.conf

# 修改 listen 指令
listen 80;

# 重启 Nginx
systemctl restart nginx
```

### 配置 HTTPS

```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

## 维护

### 查看日志

```bash
# 后端日志
journalctl -u lxd-panel -f

# Nginx 访问日志
tail -f /var/log/nginx/access.log

# Nginx 错误日志
tail -f /var/log/nginx/error.log
```

### 重启服务

```bash
# 重启后端
systemctl restart lxd-panel

# 重启 Nginx
systemctl restart nginx
```

### 数据备份

```bash
# 备份数据库
cp /opt/lxd-panel/backend/lxd_panel.db /backup/lxd_panel.db.$(date +%Y%m%d)
```

## API 文档

后端提供 RESTful API,访问 `http://服务器IP:8000/docs` 查看完整的 API 文档(Swagger UI)。

### 主要端点

- `POST /api/auth/login` - 用户登录
- `GET /api/containers` - 获取容器列表
- `POST /api/containers` - 创建容器
- `POST /api/containers/{name}/start` - 启动容器
- `POST /api/containers/{name}/stop` - 停止容器
- `GET /api/monitoring/{name}/current` - 获取当前监控数据
- `GET /api/monitoring/{name}/history` - 获取历史监控数据

## 故障排除

### 后端服务无法启动

```bash
# 查看详细错误
journalctl -u lxd-panel -n 100

# 常见问题:
# 1. Python 依赖未安装
pip3 install -r /opt/lxd-panel/backend/requirements.txt

# 2. 端口被占用
lsof -i :8000
```

### 前端无法访问

```bash
# 检查 Nginx 状态
systemctl status nginx

# 测试配置
nginx -t

# 查看错误日志
tail /var/log/nginx/error.log
```

### 监控数据不更新

1. 确保容器处于运行状态
2. 检查后端监控服务是否正常
3. 查看浏览器控制台错误(F12)

## 卸载

```bash
# 停止服务
systemctl stop lxd-panel
systemctl disable lxd-panel

# 删除文件
rm -rf /opt/lxd-panel
rm /etc/systemd/system/lxd-panel.service
rm /etc/nginx/sites-available/lxd-panel.conf
rm /etc/nginx/sites-enabled/lxd-panel.conf

# 重启 Nginx
systemctl restart nginx
```

## 贡献

欢迎提交 Issue 和 Pull Request!

## 许可证

MIT License

## 支持

如有问题,请提交 Issue 或联系开发者。

---

**祝使用愉快! 🚀**
