# LXD管理面板

一个现代化、交互式的LXD容器管理面板，提供实时监控、资源管理和直观的用户界面。

## 功能特性

### 🎨 现代化界面
- 玻璃态效果设计
- 渐变色彩方案
- 流畅的动画和过渡效果
- 响应式布局，支持各种屏幕尺寸

### 📊 实时监控
- CPU使用率实时图表
- 内存使用情况监控
- 硬盘空间使用
- 网络流量统计
- WebSocket实时数据更新（每5秒）

### 🔧 实例管理
- 启动/停止/重启容器
- 查看容器详细信息
- SSH连接信息
- NAT端口映射管理

### 🚀 扩展性
- RESTful API接口
- 模块化设计
- 易于添加新功能

## 系统要求

- **操作系统**: Ubuntu 20.04+, Debian 11+, CentOS 8+
- **LXD版本**: 4.0+
- **Python**: 3.8+
- **Nginx**: 1.18+
- **权限**: Root权限

## 快速安装

### 一键安装

```bash
# 下载并运行安装脚本
cd /path/to/zjmf-lxd-server-1.1.0
chmod +x install-panel.sh
sudo ./install-panel.sh
```

安装脚本会自动完成：
- ✅ 安装系统依赖
- ✅ 创建Python虚拟环境
- ✅ 安装Python依赖
- ✅ 生成API密钥
- ✅ 配置systemd服务
- ✅ 配置Nginx反向代理
- ✅ 设置防火墙规则
- ✅ 启动服务

### 手动安装

如果需要手动安装，请参考以下步骤：

```bash
# 1. 安装依赖
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx

# 2. 创建目录
mkdir -p /opt/lxd-panel/{backend,frontend,logs}

# 3. 复制文件
cp -r lxd-panel/backend/* /opt/lxd-panel/backend/
cp -r lxd-panel/frontend/* /opt/lxd-panel/frontend/

# 4. 安装Python依赖
cd /opt/lxd-panel/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 配置systemd和Nginx（参考安装脚本）

# 6. 启动服务
systemctl start lxd-panel
systemctl start nginx
```

## 使用指南

### 访问面板

安装完成后，通过浏览器访问：

```
http://您的服务器IP:8080
```

### 服务管理

```bash
# 启动服务
systemctl start lxd-panel

# 停止服务
systemctl stop lxd-panel

# 重启服务
systemctl restart lxd-panel

# 查看状态
systemctl status lxd-panel

# 查看日志
journalctl -u lxd-panel -f
```

### 配置说明

#### 后端配置

后端默认监听 `0.0.0.0:8000`，可通过环境变量修改：

```bash
# 编辑服务文件
vim /etc/systemd/system/lxd-panel.service

# 添加/修改环境变量
Environment="API_HOST=0.0.0.0"
Environment="API_PORT=8000"

# 重新加载并重启
systemctl daemon-reload
systemctl restart lxd-panel
```

#### 前端配置

前端由Nginx提供，默认监听端口 `8080`：

```bash
# 编辑Nginx配置
vim /etc/nginx/sites-available/lxd-panel

# 修改监听端口
listen 8080;  # 改为您想要的端口

# 重启Nginx
systemctl restart nginx
```

## API文档

### 基础端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/instances` | GET | 获取所有实例 |
| `/api/instances/{name}` | GET | 获取实例详情 |
| `/api/instances/{name}/start` | POST | 启动实例 |
| `/api/instances/{name}/stop` | POST | 停止实例 |
| `/api/instances/{name}/restart` | POST | 重启实例 |
| `/api/host/info` | GET | 获取宿主机信息 |

### WebSocket端点

```
ws://服务器IP:8000/ws/monitor
```

实时推送实例状态和资源使用情况。

### API调用示例

```bash
# 获取所有实例
curl http://localhost:8000/api/instances

# 获取实例详情
curl http://localhost:8000/api/instances/test1

# 启动实例
curl -X POST http://localhost:8000/api/instances/test1/start

# 获取宿主机信息
curl http://localhost:8000/api/host/info
```

## 目录结构

```
/opt/lxd-panel/
├── backend/              # 后端API服务
│   ├── app.py           # FastAPI主应用
│   ├── lxd_manager.py   # LXD管理器
│   ├── models.py        # 数据模型
│   ├── auth.py          # 认证模块
│   ├── requirements.txt # Python依赖
│   └── venv/            # Python虚拟环境
├── frontend/            # 前端界面
│   ├── index.html      # 主页面
│   ├── style.css       # 样式文件
│   └── app.js          # JavaScript逻辑
├── logs/               # 日志目录
│   ├── backend.log     # 后端日志
│   └── backend-error.log # 错误日志
└── api_key.txt         # API密钥
```

## 故障排除

### 服务无法启动

```bash
# 查看详细日志
journalctl -u lxd-panel -n 50

# 检查错误日志
tail -f /opt/lxd-panel/logs/backend-error.log
```

### LXD连接失败

```bash
# 检查LXD是否运行
lxc list

# 确保用户有LXD权限
usermod -aG lxd root
```

### 前端无法访问

```bash
# 检查Nginx状态
systemctl status nginx

# 测试Nginx配置
nginx -t

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

### 防火墙问题

```bash
# UFW
ufw allow 8080/tcp

# FirewallD
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload

# iptables
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

## 扩展开发

### 添加新的API端点

在 `backend/app.py` 中添加新的路由：

```python
@app.get("/api/custom/endpoint")
async def custom_endpoint():
    # 你的逻辑
    return {"message": "success"}
```

### 添加新的前端功能

1. 在 `frontend/index.html` 中添加UI元素
2. 在 `frontend/style.css` 中添加样式
3. 在 `frontend/app.js` 中添加交互逻辑

### 自定义主题

编辑 `frontend/style.css` 中的CSS变量：

```css
:root {
    --primary-blue: #4C6FFF;    /* 主色调 */
    --primary-purple: #7C3AED;  /* 辅助色 */
    --bg-primary: #0F172A;      /* 背景色 */
    /* ... */
}
```

## 安全建议

1. **修改默认端口**: 避免使用默认的8080和8000端口
2. **启用HTTPS**: 配置SSL证书以加密传输
3. **访问控制**: 配置防火墙限制访问IP
4. **定期更新**: 保持系统和依赖包更新
5. **日志监控**: 定期检查日志文件

## 更新日志

### v1.0.0 (2026-01-23)
- ✨ 初始版本发布
- 🎨 现代化UI设计
- 📊 实时资源监控
- 🔧 基础实例管理功能
- 🚀 WebSocket实时更新

## 技术栈

- **后端**: FastAPI, pylxd, WebSocket, psutil
- **前端**: HTML5, CSS3, Vanilla JavaScript, Chart.js
- **服务器**: Nginx, systemd
- **容器**: LXD/LXC

## 贡献

欢迎提交Bug报告和功能请求！

## 许可证

MIT License

## 支持

如有问题，请查看文档或提交Issue。
