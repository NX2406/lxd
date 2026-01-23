// 主应用初始化
const App = {
    init() {
        console.log('LXD管理面板初始化...');

        // 初始化认证
        Auth.init();

        // 设置标签页切换
        this.setupTabs();

        // 设置模态框
        this.setupModals();
    },

    // 设置标签页
    setupTabs() {
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;

                // 移除所有active类
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                // 添加active到当前tab
                tab.classList.add('active');
                document.getElementById(`${target}-tab`).classList.add('active');
            });
        });
    },

    // 设置模态框
    setupModals() {
        // 点击模态框外部关闭
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');

                    // 如果是详情模态框,停止监控
                    if (modal.id === 'detail-modal' && window.Monitoring) {
                        Monitoring.stopRealtime();
                    }
                }
            });
        });
    }
};

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
