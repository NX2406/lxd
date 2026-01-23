# LXD管理面板 - GitHub部署指南

本指南说明如何将LXD管理面板上传到GitHub，并使用一键脚本部署。

## 📋 前期准备

### 1. 创建GitHub仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角 `+` → `New repository`
3. 填写仓库信息：
   - **Repository name**: `lxd-panel` (或您喜欢的名称)
   - **Description**: `现代化LXD容器管理面板`
   - **Public/Private**: 建议选择 Public（方便一键安装）
   - **Initialize**: 不要勾选任何选项
4. 点击 `Create repository`

### 2. 记录仓库信息

记下您的：
- **GitHub用户名**: 例如 `zhangsan`
- **仓库名**: 例如 `lxd-panel`
- **仓库URL**: 例如 `https://github.com/zhangsan/lxd-panel`

---

## 🚀 上传代码到GitHub

### 方式一：使用命令行（推荐）

在您的Windows电脑上打开PowerShell或Git Bash：

```bash
# 进入项目目录
cd C:\Users\qq340\Downloads\zjmf-lxd-server-1.1.0\zjmf-lxd-server-1.1.0

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "初始提交: LXD管理面板v1.0.0"

# 添加远程仓库（替换为您的实际地址）
git remote add origin https://github.com/您的用户名/lxd-panel.git

# 设置主分支
git branch -M main

# 推送到GitHub
git push -u origin main
```

### 方式二：使用GitHub Desktop

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录您的GitHub账号
3. 点击 `File` → `Add Local Repository`
4. 选择项目文件夹
5. 点击 `Publish repository`
6. 选择仓库名称和可见性
7. 点击 `Publish`

### 方式三：使用网页上传

1. 在GitHub仓库页面点击 `uploading an existing file`
2. 将项目文件夹拖拽到页面
3. 填写提交信息
4. 点击 `Commit changes`

---

## ⚙️ 修改安装脚本配置

上传后，需要修改 `install-from-github.sh` 中的配置：

```bash
# 找到这两行，修改为您的实际信息
GITHUB_USER="YOUR_USERNAME"  # 改为您的GitHub用户名
GITHUB_REPO="lxd-panel"      # 改为您的仓库名
```

例如：
```bash
GITHUB_USER="zhangsan"
GITHUB_REPO="lxd-panel"
```

修改后，重新提交：
```bash
git add install-from-github.sh
git commit -m "更新GitHub配置"
git push
```

---

## 🎯 使用一键脚本安装

现在任何人都可以使用一键命令安装您的面板了！

### 方法一：直接运行（推荐）

```bash
curl -sSL https://raw.githubusercontent.com/您的用户名/lxd-panel/main/install-from-github.sh | sudo bash
```

或使用wget：
```bash
wget -qO- https://raw.githubusercontent.com/您的用户名/lxd-panel/main/install-from-github.sh | sudo bash
```

### 方法二：下载后运行

```bash
# 下载脚本
wget https://raw.githubusercontent.com/您的用户名/lxd-panel/main/install-from-github.sh

# 添加执行权限
chmod +x install-from-github.sh

# 运行
sudo ./install-from-github.sh
```

---

## 📝 更新README（可选）

建议在仓库根目录创建一个 `README.md`，方便其他人了解和使用：

```markdown
# LXD管理面板

现代化、交互式的LXD容器管理面板，提供实时监控和直观的用户界面。

## 功能特性

- 🎨 玻璃态现代化UI设计
- 📊 实时资源监控（CPU、内存、硬盘、网络）
- 🔧 容器管理（启动、停止、重启）
- ⚡ WebSocket实时数据更新
- 🔌 完整的RESTful API

## 一键安装

```bash
curl -sSL https://raw.githubusercontent.com/您的用户名/lxd-panel/main/install-from-github.sh | sudo bash
```

安装完成后访问：`http://服务器IP:8080`

## 系统要求

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- LXD 4.0+
- Python 3.8+

## 文档

- [使用说明](lxd-panel/README.md)
- [API文档](lxd-panel/API.md)

## 许可证

MIT License
```

---

## 🔄 后续更新流程

当您修改代码后，推送更新到GitHub：

```bash
# 添加修改
git add .

# 提交
git commit -m "描述您的修改"

# 推送
git push
```

用户重新运行一键脚本即可获取最新版本。

---

## 📂 推荐的文件结构

上传到GitHub的文件结构应该是：

```
lxd-panel/                    # 仓库根目录
├── .gitignore               # Git忽略文件
├── README.md                # 仓库说明（可选）
├── install-from-github.sh   # GitHub一键安装脚本 ⭐
├── install-panel.sh         # 本地安装脚本
├── GitHub部署指南.md         # 本文档
└── lxd-panel/               # 面板代码
    ├── backend/             # 后端代码
    │   ├── app.py
    │   ├── lxd_manager.py
    │   ├── models.py
    │   ├── auth.py
    │   └── requirements.txt
    ├── frontend/            # 前端代码
    │   ├── index.html
    │   ├── style.css
    │   └── app.js
    ├── README.md           # 详细使用说明
    └── API.md              # API文档
```

---

## ⚠️ 注意事项

### 私有仓库

如果您的仓库是私有的，一键安装脚本需要进行身份验证。有两种方案：

**方案1：使用Personal Access Token**
```bash
# 在下载URL中添加token
git clone https://TOKEN@github.com/用户名/仓库名.git
```

**方案2：改为公开仓库**（推荐）
- 如果不包含敏感信息，建议设为公开
- 方便他人使用一键安装

### 安全建议

1. **不要提交敏感信息**：
   - `api_key.txt` 已在 `.gitignore` 中排除
   - 不要在代码中硬编码密码

2. **API密钥**：
   - 每次安装都会自动生成新的API密钥
   - 不需要手动配置

3. **定期更新**：
   - 及时修复安全漏洞
   - 更新依赖包版本

---

## 🎯 完整示例

假设您的GitHub用户名是 `zhangsan`，仓库名是 `lxd-panel`：

### 1. 上传代码
```bash
cd C:\Users\qq340\Downloads\zjmf-lxd-server-1.1.0\zjmf-lxd-server-1.1.0
git init
git add .
git commit -m "初始提交"
git remote add origin https://github.com/zhangsan/lxd-panel.git
git push -u origin main
```

### 2. 修改脚本配置
编辑 `install-from-github.sh`：
```bash
GITHUB_USER="zhangsan"
GITHUB_REPO="lxd-panel"
```

### 3. 推送更新
```bash
git add install-from-github.sh
git commit -m "更新配置"
git push
```

### 4. 使用一键安装
在任何Linux服务器上：
```bash
curl -sSL https://raw.githubusercontent.com/zhangsan/lxd-panel/main/install-from-github.sh | sudo bash
```

---

## ❓ 常见问题

### Q: 提示"Permission denied"？
A: 确保使用 `sudo` 运行安装脚本

### Q: 下载速度慢？
A: 可以使用国内GitHub镜像，或下载ZIP包后本地安装

### Q: 修改代码后如何更新？
A: 在服务器上删除 `/opt/lxd-panel`，重新运行一键脚本

### Q: 如何备份数据？
A: 备份 `/opt/lxd-panel` 目录即可

---

## 📞 技术支持

- 查看详细文档：`lxd-panel/README.md`
- API文档：`lxd-panel/API.md`
- 提交Issue：在GitHub仓库的Issues页面

---

**制作时间**: 2026-01-23  
**版本**: v1.0.0
