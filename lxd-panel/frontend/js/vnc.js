// VNC模块
const VNC = {
    token: null,
    websocket: null,

    // 打开VNC控制台
    async openVNC(containerName) {
        try {
            const result = await api.getVNCToken(containerName);
            this.token = result.token;

            document.getElementById('vnc-modal').classList.add('active');

            // 这里应该初始化noVNC客户端
            // 由于noVNC需要特殊配置,这里只显示说明
            const screen = document.getElementById('vnc-screen');
            screen.innerHTML = `
                <p class="vnc-notice">VNC功能需要在容器中安装VNC服务器</p>
                <p class="vnc-notice">安装方法:</p>
                <p class="vnc-notice">Debian/Ubuntu: apt-get install x11vnc</p>
                <p class="vnc-notice">CentOS/RHEL: yum install tigervnc-server</p>
                <p class="vnc-notice">然后启动VNC服务: x11vnc -display :0 -forever</p>
                <br>
                <p class="vnc-notice">Token: ${this.token}</p>
                <p class="vnc-notice">容器: ${containerName}</p>
            `;
        } catch (error) {
            alert('获取VNC令牌失败: ' + error.message);
        }
    }
};

// 全局函数
function closeVNCModal() {
    document.getElementById('vnc-modal').classList.remove('active');
}

// VNC按钮点击事件
document.addEventListener('DOMContentLoaded', () => {
    const vncBtn = document.getElementById('vnc-btn');
    if (vncBtn) {
        vncBtn.addEventListener('click', () => {
            if (Containers.currentContainer) {
                VNC.openVNC(Containers.currentContainer);
            }
        });
    }
});
