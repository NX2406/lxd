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
    },
    hostInfo: null
};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('LXD管理面板启动...');
    initTabs();
    initCharts();
    initEventListeners();
    loadInstances();
    connectWebSocket();
});

// ========== 事件监听器 ==========
function initEventListeners() {
    // 实例选择器
    const selector = document.getElementById('instanceSelector');
    if (selector) {
        selector.addEventListener('change', (e) => {
            const selectedName = e.target.value;
            if (selectedName) {
                selectInstance(selectedName);
            }
        });
    }

    // 创建实例按钮
    const createBtn = document.getElementById('createInstanceBtn');
    if (createBtn) {
        createBtn.addEventListener('click', () => openCreateModal());
    }

    // 弹窗关闭
    const modalClose = document.getElementById('modalClose');
    if (modalClose) {
        modalClose.addEventListener('click', () => closeCreateModal());
    }

    // 弹窗取消按钮
    const cancelBtn = document.getElementById('cancelCreateBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => closeCreateModal());
    }

    // 弹窗提交按钮
    const submitBtn = document.getElementById('submitCreateBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', () => submitCreateInstance());
    }

    // 批量启动按钮
    const batchStartBtn = document.getElementById('batchStartBtn');
    if (batchStartBtn) {
        batchStartBtn.addEventListener('click', () => batchStartInstances());
    }

    // 批量停止按钮
    const batchStopBtn = document.getElementById('batchStopBtn');
    if (batchStopBtn) {
        batchStopBtn.addEventListener('click', () => batchStopInstances());
    }

    // 删除实例按钮
    const deleteBtn = document.getElementById('deleteInstanceBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => deleteCurrentInstance());
    }

    // 点击弹窗背景关闭
    const modal = document.getElementById('createModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeCreateModal();
            }
        });
    }
}

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

        // 更新实例选择器
        updateInstanceSelector();

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

function updateInstanceSelector() {
    const selector = document.getElementById('instanceSelector');
    if (!selector) return;

    // 清空现有选项
    selector.innerHTML = '';

    // 添加实例选项
    state.instances.forEach(instance => {
        const option = document.createElement('option');
        option.value = instance.name;
        option.textContent = instance.name;
        selector.appendChild(option);
    });

    // 设置当前选中的实例
    if (state.currentInstance) {
        selector.value = state.currentInstance.info.name;
    }
}

async function selectInstance(name) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/instances/${name}`);
        if (!response.ok) throw new Error('获取实例详情失败');

        const instance = await response.json();
        state.currentInstance = instance;
        updateUI(instance);

        // 更新选择器
        const selector = document.getElementById('instanceSelector');
        if (selector) {
            selector.value = name;
        }
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
        statusBadge.querySelector('.status-dot').style.background = 'var(--success-green)';
    } else {
        statusBadge.innerHTML = '<span class="status-dot"></span>已停止';
        statusBadge.querySelector('.status-dot').style.background = 'var(--text-secondary)';
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

function updateHostStats(hostInfo) {
    if (!hostInfo) return;

    state.hostInfo = hostInfo;

    // 更新宿主机CPU
    const hostCPU = document.getElementById('hostCPU');
    if (hostCPU) {
        hostCPU.textContent = `${hostInfo.cpu_usage.toFixed(1)}%`;
    }

    // 更新宿主机内存
    const hostMemory = document.getElementById('hostMemory');
    if (hostMemory) {
        const memUsedGB = (hostInfo.memory_used / 1024).toFixed(1);
        const memTotalGB = (hostInfo.memory_total / 1024).toFixed(1);
        hostMemory.textContent = `${memUsedGB}GB / ${memTotalGB}GB`;
    }

    // 更新宿主机硬盘
    const hostDisk = document.getElementById('hostDisk');
    if (hostDisk) {
        const diskUsedGB = (hostInfo.disk_used / (1024 ** 3)).toFixed(1);
        const diskTotalGB = (hostInfo.disk_total / (1024 ** 3)).toFixed(1);
        hostDisk.textContent = `${diskUsedGB}GB / ${diskTotalGB}GB`;
    }
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
    if (data.type === 'update' && data.data) {
        const { instances, host } = data.data;

        // 更新宿主机信息
        if (host) {
            updateHostStats(host);
        }

        // 更新实例信息
        if (instances && instances.length > 0) {
            // 如果有当前选中的实例，更新其数据
            if (state.currentInstance) {
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
            } else {
                // 如果还没有选中实例，选择第一个
                selectInstance(instances[0].name);
            }
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

// ========== 创建实例 ==========
function openCreateModal() {
    const modal = document.getElementById('createModal');
    if (modal) {
        modal.classList.add('show');
    }
}

function closeCreateModal() {
    const modal = document.getElementById('createModal');
    if (modal) {
        modal.classList.remove('show');
    }
    // 重置表单
    resetCreateForm();
}

function resetCreateForm() {
    const form = document.getElementById('createInstanceForm');
    if (form) {
        form.reset();
    }
}

async function submitCreateInstance() {
    // 获取表单数据
    const name = document.getElementById('instanceName').value.trim();
    const osType = document.getElementById('osType').value;
    const osVersion = document.getElementById('osVersion').value;
    const cpu = parseInt(document.getElementById('cpuCores').value);
    const memory = parseInt(document.getElementById('memorySize').value);
    const disk = parseInt(document.getElementById('diskSize').value);
    const sshPort = parseInt(document.getElementById('sshPort').value);
    const natStart = parseInt(document.getElementById('natStart').value);
    const natEnd = parseInt(document.getElementById('natEnd').value);

    // 验证
    if (!name) {
        showToast('请输入实例名称', 'warning');
        return;
    }

    if (cpu < 1 || cpu > 16) {
        showToast('CPU核心数必须在1-16之间', 'warning');
        return;
    }

    if (memory < 512) {
        showToast('内存大小至少需要512MB', 'warning');
        return;
    }

    if (disk < 10) {
        showToast('硬盘大小至少需要10GB', 'warning');
        return;
    }

    if (sshPort < 1024 || sshPort > 65535) {
        showToast('SSH端口必须在1024-65535之间', 'warning');
        return;
    }

    if (natStart >= natEnd) {
        showToast('NAT起始端口必须小于结束端口', 'warning');
        return;
    }

    try {
        showToast('正在创建实例，请稍候...', 'info');

        const response = await fetch(`${CONFIG.API_BASE}/api/instances`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                os_type: osType,
                os_version: osVersion,
                cpu,
                memory,
                disk,
                ssh_port: sshPort,
                nat_start: natStart,
                nat_end: natEnd
            })
        });

        if (!response.ok) throw new Error('创建失败');

        const result = await response.json();

        if (result.success) {
            showToast('实例创建成功！', 'success');
            closeCreateModal();
            // 刷新实例列表
            setTimeout(() => {
                loadInstances();
            }, 2000);
        } else {
            showToast(result.message || '创建失败', 'error');
        }
    } catch (error) {
        console.error('创建实例失败:', error);
        showToast('创建实例失败', 'error');
    }
}

// ========== 批量操作 ==========
async function batchStartInstances() {
    if (!confirm('确定要批量启动所有已停止的实例吗？')) {
        return;
    }

    try {
        showToast('正在批量启动实例...', 'info');

        const response = await fetch(`${CONFIG.API_BASE}/api/instances/batch/start`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('操作失败');

        const result = await response.json();

        if (result.success) {
            showToast(result.message || '批量启动成功', 'success');
            // 刷新数据
            setTimeout(() => {
                loadInstances();
            }, 2000);
        } else {
            showToast(result.message || '批量启动失败', 'error');
        }
    } catch (error) {
        console.error('批量启动失败:', error);
        showToast('批量启动失败', 'error');
    }
}

async function batchStopInstances() {
    if (!confirm('确定要批量停止所有正在运行的实例吗？')) {
        return;
    }

    try {
        showToast('正在批量停止实例...', 'info');

        const response = await fetch(`${CONFIG.API_BASE}/api/instances/batch/stop`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('操作失败');

        const result = await response.json();

        if (result.success) {
            showToast(result.message || '批量停止成功', 'success');
            // 刷新数据
            setTimeout(() => {
                loadInstances();
            }, 2000);
        } else {
            showToast(result.message || '批量停止失败', 'error');
        }
    } catch (error) {
        console.error('批量停止失败:', error);
        showToast('批量停止失败', 'error');
    }
}

async function deleteCurrentInstance() {
    if (!state.currentInstance) {
        showToast('请先选择一个实例', 'warning');
        return;
    }

    const name = state.currentInstance.info.name;

    if (!confirm(`确定要删除实例 "${name}" 吗？此操作不可恢复！`)) {
        return;
    }

    try {
        showToast('正在删除实例...', 'info');

        const response = await fetch(`${CONFIG.API_BASE}/api/instances/${name}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('删除失败');

        const result = await response.json();

        if (result.success) {
            showToast('实例删除成功', 'success');
            state.currentInstance = null;
            // 刷新实例列表
            setTimeout(() => {
                loadInstances();
            }, 1000);
        } else {
            showToast(result.message || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除实例失败:', error);
        showToast('删除实例失败', 'error');
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
