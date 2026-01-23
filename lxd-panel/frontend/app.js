/**
 * LXD管理面板 - 前端应用逻辑
 * 实现实时数据更新、图表渲染和用户交互
 */

// 配置
const CONFIG = {
    // API地址 - 根据实际部署修改
    API_BASE: window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : `http://${window.location.hostname}:8000`,
    WS_URL: window.location.hostname === 'localhost'
        ? 'ws://localhost:8000/ws/monitor'
        : `ws://${window.location.hostname}:8000/ws/monitor`,
    UPDATE_INTERVAL: 5000, // 5秒更新一次
    CHART_DATA_POINTS: 20, // 图表显示数据点数量
};

// 全局状态
const state = {
    currentInstance: null,
    instances: [],
    charts: {},
    ws: null,
    chartData: {
        cpu: [],
        memory: [],
        disk: [],
        network: []
    }
};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('LXD管理面板启动...');
    initTabs();
    initCharts();
    loadInstances();
    connectWebSocket();
});

// ========== 标签切换 ==========
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // 移除所有active类
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    // 添加active类到当前标签
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ========== Chart.js图表初始化 ==========
function initCharts() {
    const chartConfig = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: { enabled: false }
        },
        scales: {
            x: { display: false },
            y: {
                display: false,
                min: 0,
                max: 100,
                beginAtZero: true
            }
        },
        elements: {
            line: {
                tension: 0.4,
                borderWidth: 2
            },
            point: {
                radius: 0
            }
        },
        animation: {
            duration: 750
        }
    };

    // CPU图表
    state.charts.cpu = new Chart(document.getElementById('cpuChart'), {
        type: 'line',
        data: {
            labels: Array(CONFIG.CHART_DATA_POINTS).fill(''),
            datasets: [{
                data: Array(CONFIG.CHART_DATA_POINTS).fill(0),
                borderColor: '#60A5FA',
                backgroundColor: createGradient('cpuChart', '#60A5FA'),
                fill: true
            }]
        },
        options: chartConfig
    });

    // 内存图表
    state.charts.memory = new Chart(document.getElementById('memoryChart'), {
        type: 'line',
        data: {
            labels: Array(CONFIG.CHART_DATA_POINTS).fill(''),
            datasets: [{
                data: Array(CONFIG.CHART_DATA_POINTS).fill(0),
                borderColor: '#34D399',
                backgroundColor: createGradient('memoryChart', '#34D399'),
                fill: true
            }]
        },
        options: chartConfig
    });

    // 硬盘图表
    state.charts.disk = new Chart(document.getElementById('diskChart'), {
        type: 'line',
        data: {
            labels: Array(CONFIG.CHART_DATA_POINTS).fill(''),
            datasets: [{
                data: Array(CONFIG.CHART_DATA_POINTS).fill(0),
                borderColor: '#22D3EE',
                backgroundColor: createGradient('diskChart', '#22D3EE'),
                fill: true
            }]
        },
        options: chartConfig
    });

    // 流量图表
    state.charts.network = new Chart(document.getElementById('networkChart'), {
        type: 'line',
        data: {
            labels: Array(CONFIG.CHART_DATA_POINTS).fill(''),
            datasets: [{
                data: Array(CONFIG.CHART_DATA_POINTS).fill(0),
                borderColor: '#FBBF24',
                backgroundColor: createGradient('networkChart', '#FBBF24'),
                fill: true
            }]
        },
        options: chartConfig
    });
}

function createGradient(canvasId, color) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, color + '40'); // 25% opacity
    gradient.addColorStop(1, color + '00'); // 0% opacity
    return gradient;
}

// ========== 数据加载 ==========
async function loadInstances() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/instances`);
        if (!response.ok) throw new Error('获取实例列表失败');

        state.instances = await response.json();

        if (state.instances.length > 0) {
            // 默认选择第一个实例
            selectInstance(state.instances[0].name);
        } else {
            showToast('暂无实例', 'warning');
            updateUINoInstance();
        }
    } catch (error) {
        console.error('加载实例失败:', error);
        showToast('连接后端失败，请检查服务', 'error');
        updateUINoInstance();
    }
}

async function selectInstance(name) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/instances/${name}`);
        if (!response.ok) throw new Error('获取实例详情失败');

        const instance = await response.json();
        state.currentInstance = instance;
        updateUI(instance);
    } catch (error) {
        console.error('加载实例详情失败:', error);
        showToast('加载实例详情失败', 'error');
    }
}

// ========== UI更新 ==========
function updateUI(instance) {
    const { info, resources, ssh_port, nat_ports, root_password } = instance;

    // 更新头部信息
    document.getElementById('instanceName').textContent = info.name || '未知实例';
    document.getElementById('instanceId').textContent = `实例ID: ${info.name || '--'}`;
    document.getElementById('instanceArch').textContent = `架构: ${info.architecture || '--'}`;

    // 更新状态
    const statusBadge = document.getElementById('instanceStatus');
    const statusDot = statusBadge.querySelector('.status-dot');
    if (info.status === 'Running') {
        statusBadge.innerHTML = '<span class="status-dot"></span>运行中';
        statusDot.style.background = 'var(--success-green)';
    } else {
        statusBadge.innerHTML = '<span class="status-dot"></span>已停止';
        statusDot.style.background = 'var(--text-secondary)';
    }

    // 更新快速资源显示
    document.getElementById('quickCPU').textContent = `${resources.cpu_percent.toFixed(1)}%`;
    document.getElementById('quickMemory').textContent = `${Math.round(resources.memory_used)}MB`;
    document.getElementById('quickDisk').textContent = `${Math.round(resources.disk_used / 1024)}GB`;

    // 更新侧边栏
    document.getElementById('sidebarPassword').textContent = root_password || '--';
    document.getElementById('sidebarSSH').textContent = ssh_port || '--';
    document.getElementById('storageTotalSidebar').textContent = `${resources.memory_total}MB`;

    // 更新资源图表值
    document.getElementById('cpuValue').textContent = `${resources.cpu_percent.toFixed(1)}% / 使用中`;
    document.getElementById('memoryValue').textContent = `${Math.round(resources.memory_used)} MB / ${resources.memory_total}MB`;
    document.getElementById('diskValue').textContent = `${Math.round(resources.disk_used / 1024)} GB / ${Math.round(resources.disk_total / 1024)}GB`;
    document.getElementById('networkValue').textContent = `${(resources.network_tx / 1024).toFixed(2)} GB / 流量`;

    // 更新图表数据
    updateChartData('cpu', resources.cpu_percent);
    updateChartData('memory', (resources.memory_used / resources.memory_total) * 100);
    updateChartData('disk', (resources.disk_used / resources.disk_total) * 100);
    updateChartData('network', Math.min((resources.network_tx / 10240) * 100, 100)); // 假设10GB限制

    // 更新NAT信息
    const natInfo = document.getElementById('natInfo');
    if (nat_ports) {
        natInfo.innerHTML = `
            <div class="info-item">
                <span class="info-label">映射端口范围:</span>
                <span class="info-value">${nat_ports}</span>
            </div>
            <div class="info-item">
                <span class="info-label">协议:</span>
                <span class="info-value">TCP/UDP</span>
            </div>
        `;
    } else {
        natInfo.innerHTML = '<p>未配置NAT端口转发</p>';
    }
}

function updateUINoInstance() {
    document.getElementById('instanceName').textContent = '无可用实例';
    document.getElementById('instanceId').textContent = '实例ID: --';
    document.getElementById('instanceArch').textContent = '架构: --';
    document.getElementById('instanceStatus').innerHTML = '<span class="status-dot"></span>无实例';
}

function updateChartData(chartName, value) {
    const chart = state.charts[chartName];
    if (!chart) return;

    const data = chart.data.datasets[0].data;
    data.push(value);
    if (data.length > CONFIG.CHART_DATA_POINTS) {
        data.shift();
    }
    chart.update('none'); // 无动画更新
}

// ========== WebSocket实时监控 ==========
function connectWebSocket() {
    try {
        state.ws = new WebSocket(CONFIG.WS_URL);

        state.ws.onopen = () => {
            console.log('WebSocket连接已建立');
            showToast('实时监控已连接', 'success');
        };

        state.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };

        state.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
            showToast('实时监控连接失败', 'error');
        };

        state.ws.onclose = () => {
            console.log('WebSocket连接已关闭，5秒后重连...');
            setTimeout(connectWebSocket, 5000);
        };
    } catch (error) {
        console.error('WebSocket连接失败:', error);
        setTimeout(connectWebSocket, 5000);
    }
}

function handleWebSocketMessage(data) {
    if (data.type === 'update' && data.data.instances) {
        const instances = data.data.instances;

        // 如果有当前选中的实例，更新其数据
        if (state.currentInstance && instances.length > 0) {
            const currentData = instances.find(i => i.name === state.currentInstance.info.name);
            if (currentData) {
                // 构造与API返回相同的数据结构
                const updatedInstance = {
                    info: {
                        name: currentData.name,
                        status: currentData.status,
                        ipv4: currentData.ipv4,
                        architecture: state.currentInstance.info.architecture
                    },
                    resources: currentData.resources,
                    ssh_port: currentData.ssh_port,
                    nat_ports: currentData.nat_ports,
                    root_password: state.currentInstance.root_password
                };
                state.currentInstance = updatedInstance;
                updateUI(updatedInstance);
            }
        } else if (instances.length > 0 && !state.currentInstance) {
            // 如果还没有选中实例，选择第一个
            selectInstance(instances[0].name);
        }
    }
}

// ========== 实例控制 ==========
async function controlInstance(action) {
    if (!state.currentInstance) {
        showToast('请先选择一个实例', 'warning');
        return;
    }

    const name = state.currentInstance.info.name;
    const actionMap = {
        'start': '启动',
        'stop': '停止',
        'restart': '重启'
    };

    try {
        showToast(`正在${actionMap[action]}实例...`, 'info');

        const response = await fetch(`${CONFIG.API_BASE}/api/instances/${name}/${action}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('操作失败');

        const result = await response.json();

        if (result.success) {
            showToast(`实例${actionMap[action]}成功`, 'success');
            // 延迟刷新数据
            setTimeout(() => selectInstance(name), 2000);
        } else {
            showToast(result.message || '操作失败', 'error');
        }
    } catch (error) {
        console.error('控制实例失败:', error);
        showToast(`${actionMap[action]}实例失败`, 'error');
    }
}

// ========== Toast通知 ==========
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 导出函数供HTML调用
window.controlInstance = controlInstance;
window.selectInstance = selectInstance;
