// 认证模块
const Auth = {
    // 初始化
    init() {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // 检查登录状态
        this.checkAuth();
    },

    // 检查认证状态
    async checkAuth() {
        const token = localStorage.getItem('token');

        if (!token) {
            this.showLoginPage();
            return false;
        }

        try {
            await api.getCurrentUser();
            this.showMainPage();
            return true;
        } catch (error) {
            this.showLoginPage();
            return false;
        }
    },

    // 处理登录
    async handleLogin(e) {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-error');

        try {
            const result = await api.login(username, password);
            api.setToken(result.access_token);

            errorDiv.textContent = '';
            this.showMainPage();

            // 加载容器列表
            if (window.Containers) {
                Containers.loadContainers();
            }
        } catch (error) {
            errorDiv.textContent = error.message || '登录失败';
        }
    },

    // 登出
    async logout() {
        try {
            await api.logout();
        } finally {
            this.showLoginPage();
        }
    },

    // 显示登录页面
    showLoginPage() {
        document.getElementById('login-page').style.display = 'block';
        document.getElementById('main-page').style.display = 'none';
    },

    // 显示主页面
    showMainPage() {
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('main-page').style.display = 'block';
    }
};

// 登出函数(供HTML调用)
function logout() {
    Auth.logout();
}
