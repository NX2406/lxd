# GitHub部署完整指南

## 📋 步骤清单

### 第一步: 上传新文件到GitHub ✅

您需要将以下**新创建的文件**提交到GitHub仓库：

1. `quick_install.sh` - 一键部署脚本
2. `DEPLOY.md` - 部署文档
3. `GITHUB_SETUP.md` - 本文件（可选）

**操作命令**:

```bash
cd C:\Users\qq340\.gemini\antigravity\scratch\lxd-panel

# 添加新文件
git add quick_install.sh DEPLOY.md GITHUB_SETUP.md

# 提交
git commit -m "添加一键部署脚本和文档"

# 推送到GitHub
git push origin main
```

### 第二步: 修改quick_install.sh中的仓库地址

**在GitHub网页上编辑** `quick_install.sh` 文件:

找到第20行：
```bash
GITHUB_REPO="https://github.com/你的用户名/lxd-panel.git"
```

修改为您的实际仓库地址，例如：
```bash
GITHUB_REPO="https://github.com/yourname/lxd-panel.git"
```

保存并提交。

### 第三步: 在Linux服务器上部署

现在您可以在任何Linux服务器上使用一键命令安装了！

**一键部署命令**（替换为您的GitHub用户名和仓库名）：

```bash
curl -fsSL https://raw.githubusercontent.com/yourname/lxd-panel/main/quick_install.sh | bash
```

## 🎯 完整部署示例

假设您的GitHub仓库是: `https://github.com/NX2406/lxd`

### 1. 修改quick_install.sh

```bash
GITHUB_REPO="https://github.com/NX2406/lxd.git"
```

### 2. 在服务器上执行

```bash
# SSH登录到服务器
ssh root@your-server-ip

# 一键安装
curl -fsSL https://raw.githubusercontent.com/NX2406/lxd/main/quick_install.sh | bash

# 等待2-5分钟安装完成
```

### 3. 访问面板

安装完成后，浏览器访问：
```
http://your-server-ip
```

登录账号：
- 用户名: `admin`
- 密码: `admin`

## 📝 README更新建议

建议在您的GitHub仓库的README.md顶部添加：

```markdown
# LXD 管理面板

## 快速开始

一键部署到您的Linux服务器：

\`\`\`bash
curl -fsSL https://raw.githubusercontent.com/yourname/lxd-panel/main/quick_install.sh | bash
\`\`\`

安装完成后访问 `http://服务器IP`，使用 `admin/admin` 登录。
```

## 🔍 验证部署

部署完成后，在服务器上检查：

```bash
# 检查服务状态
systemctl status lxd-panel
systemctl status nginx

# 查看日志
journalctl -u lxd-panel -n 50

# 测试API
curl http://localhost:8000/health
```

## 💡 提示

- 确保服务器80端口开放
- 首次登录后立即修改默认密码
- 建议配置HTTPS证书
- 定期备份数据库：`/opt/lxd-panel/backend/lxd_panel.db`

---

**现在您的LXD管理面板已经可以通过一行命令部署了！** 🎉
