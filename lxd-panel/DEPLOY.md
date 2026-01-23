# LXD管理面板 - 快速部署指南

## 🚀 一键部署（推荐）

### 方法1: 使用curl一键安装

在您的Linux服务器上执行以下命令：

```bash
curl -fsSL https://raw.githubusercontent.com/NX2406/lxd/main/lxd-panel/quick_install.sh | bash
```

或者使用wget：

```bash
wget -qO- https://raw.githubusercontent.com/NX2406/lxd/main/lxd-panel/quick_install.sh | bash
```

### 方法2: 手动克隆安装

```bash
# 1. 克隆仓库
git clone https://github.com/NX2406/lxd.git
cd lxd

# 2. 运行安装脚本
chmod +x install_panel.sh
./install_panel.sh
```

## ⚙️ 安装步骤说明

安装脚本会自动完成：

1. ✅ 检测操作系统（支持Ubuntu/Debian/CentOS）
2. ✅ 安装系统依赖（Python3, pip, Nginx, LXD, jq, bc）
3. ✅ 检查并初始化LXD环境
4. ✅ 安装Python依赖包
5. ✅ 配置systemd服务（自动启动）
6. ✅ 配置Nginx反向代理
7. ✅ 启动所有服务

**安装时间**: 约2-5分钟

## 📝 前置要求

- **操作系统**: Ubuntu 20.04+ / Debian 11+ / CentOS 7+
- **权限**: Root用户
- **网络**: 需要访问GitHub和pypi.org

## 🎯 安装完成后

### 访问面板

```
访问地址: http://你的服务器IP
默认用户名: admin
默认密码: admin
```

**⚠️ 重要提示**: 首次登录后请立即修改默认密码！

### 检查服务状态

```bash
# 查看后端服务状态
systemctl status lxd-panel

# 查看Nginx状态
systemctl status nginx

# 查看后端日志
journalctl -u lxd-panel -f
```

## 🔧 配置HTTPS（可选）

```bash
# 安装certbot
apt-get install certbot python3-certbot-nginx

# 获取SSL证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

## 📊 使用示例

### 1. 创建容器

虽然面板已实现创建API，但建议先使用原bash脚本创建容器：

```bash
# 使用原脚本创建容器
bash /path/to/your/panel.txt
# 选择选项1创建容器
```

创建后，容器会自动显示在Web面板中。

### 2. 管理容器

在Web面板中可以：
- 查看所有容器列表
- 启动/停止/重启容器
- 删除容器
- 重装系统
- 查看详细信息（IP、密码、端口等）

### 3. 监控数据

点击容器卡片查看：
- 实时CPU/内存/网络/磁盘使用率
- 过去24小时历史数据图表
- 自动每5秒刷新

## 🐛 故障排除

### 后端服务无法启动

```bash
# 查看详细日志
journalctl -u lxd-panel -n 100 --no-pager

# 检查端口占用
lsof -i :8000

# 手动安装依赖
cd /opt/lxd-panel/backend
pip3 install -r requirements.txt
```

### Nginx无法访问

```bash
# 测试配置
nginx -t

# 查看错误日志
tail -f /var/log/nginx/error.log

# 检查80端口
netstat -tlnp | grep :80
```

### LXD连接失败

```bash
# 检查LXD状态
lxc list

# 重新初始化LXD
lxd init --auto
```

## 🔄 更新面板

```bash
cd /opt/lxd-panel
git pull
systemctl restart lxd-panel
systemctl restart nginx
```

## 🗑️ 卸载

```bash
# 停止服务
systemctl stop lxd-panel
systemctl disable lxd-panel

# 删除文件
rm -rf /opt/lxd-panel
rm /etc/systemd/system/lxd-panel.service
rm /etc/nginx/sites-available/lxd-panel.conf
rm /etc/nginx/sites-enabled/lxd-panel.conf

# 重启Nginx
systemctl restart nginx
```

## 📞 获取帮助

如遇问题，请：
1. 查看日志：`journalctl -u lxd-panel -n 50`
2. 检查GitHub Issues
3. 提交新Issue并附上错误信息

---

**祝使用愉快！** 🎉
