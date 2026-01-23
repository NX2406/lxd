// 容器管理模块
const Containers = {
    currentContainer: null,

    // 加载容器列表
    async loadContainers() {
        try {
            const containers = await api.listContainers();
            this.renderContainerList(containers);
            this.updateResourceSummary(containers);
        } catch (error) {
            console.error('加载容器列表失败:', error);
            alert('加载容器列表失败: ' + error.message);
        }
    },

    // 渲染容器列表
    renderContainerList(containers) {
        const listDiv = document.getElementById('container-list');

        if (containers.length === 0) {
            listDiv.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">暂无容器, 点击"创建容器"开始使用</p>';
            return;
        }

        listDiv.innerHTML = containers.map(container => `
            <div class="container-card" onclick="Containers.showDetail('${container.name}')">
                <div class="container-header">
                    <span class="container-name">${container.name}</span>
                    <span class="badge ${container.status === 'Running' ? 'badge-running' : 'badge-stopped'}">
                        ${container.status}
                    </span>
                </div>
                <div class="container-stats">
                    <div class="stat-row">
                        <span class="label">IP地址:</span>
                        <span>${container.ip_address || '--'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="label">CPU:</span>
                        <span>${container.cpu} 核</span>
                    </div>
                    <div class="stat-row">
                        <span class="label">内存:</span>
                        <span>${container.memory} MB</span>
                    </div>
                    <div class="stat-row">
                        <span class="label">SSH端口:</span>
                        <span>${container.ssh_port || '--'}</span>
                    </div>
                </div>
                <div class="container-actions" onclick="event.stopPropagation()">
                    ${container.status === 'Running'
                ? `<button class="btn btn-sm btn-warning" onclick="Containers.stopContainer('${container.name}')">停止</button>`
                : `<button class="btn btn-sm btn-success" onclick="Containers.startContainer('${container.name}')">启动</button>`
            }
                    <button class="btn btn-sm btn-secondary" onclick="Containers.restartContainer('${container.name}')">重启</button>
                    <button class="btn btn-sm btn-danger" onclick="Containers.deleteContainer('${container.name}')">删除</button>
                </div>
            </div>
        `).join('');
    },

    // 更新资源汇总
    updateResourceSummary(containers) {
        let totalCPU = 0;
        let totalMemory = 0;

        containers.forEach(container => {
            totalCPU += parseFloat(container.cpu) || 0;
            totalMemory += parseInt(container.memory) || 0;
        });

        document.getElementById('total-cpu').textContent = `${totalCPU} 核`;
        document.getElementById('total-memory').textContent = `${totalMemory} MB`;
    },

    // 启动容器
    async startContainer(name) {
        try {
            await api.startContainer(name);
            alert(`容器 ${name} 已启动`);
            this.loadContainers();
        } catch (error) {
            alert('启动失败: ' + error.message);
        }
    },

    // 停止容器
    async stopContainer(name) {
        try {
            await api.stopContainer(name);
            alert(`容器 ${name} 已停止`);
            this.loadContainers();
        } catch (error) {
            alert('停止失败: ' + error.message);
        }
    },

    // 重启容器
    async restartContainer(name) {
        try {
            await api.restartContainer(name);
            alert(`容器 ${name} 已重启`);
            this.loadContainers();
        } catch (error) {
            alert('重启失败: ' + error.message);
        }
    },

    // 删除容器
    async deleteContainer(name) {
        if (!confirm(`确定要删除容器 ${name} 吗? 此操作不可恢复!`)) {
            return;
        }

        try {
            await api.deleteContainer(name);
            alert(`容器 ${name} 已删除`);
            this.loadContainers();
        } catch (error) {
            alert('删除失败: ' + error.message);
        }
    },

    // 显示容器详情
    async showDetail(name) {
        this.currentContainer = name;

        try {
            const container = await api.getContainer(name);

            document.getElementById('detail-title').textContent = `容器: ${name}`;
            document.getElementById('detail-status').textContent = container.status;
            document.getElementById('detail-status').className = `badge ${container.status === 'Running' ? 'badge-running' : 'badge-stopped'}`;
            document.getElementById('detail-ip').textContent = container.ip_address || '--';
            document.getElementById('detail-ssh-port').textContent = container.ssh_port || '--';
            document.getElementById('detail-password').textContent = container.password || '--';

            document.getElementById('detail-modal').classList.add('active');

            // 加载监控数据
            if (container.status === 'Running' && window.Monitoring) {
                Monitoring.loadCharts(name);
                Monitoring.startRealtime(name);
            }
        } catch (error) {
            alert('加载容器详情失败: ' + error.message);
        }
    },

    // 创建容器
    async createContainer(config) {
        try {
            await api.createContainer(config);
            alert('容器创建成功!');
            closeCreateModal();
            this.loadContainers();
        } catch (error) {
            alert('创建失败: ' + error.message);
        }
    }
};

// 全局函数(供HTML调用)
function refreshContainers() {
    Containers.loadContainers();
}

function showCreateModal() {
    document.getElementById('create-modal').classList.add('active');
}

function closeCreateModal() {
    document.getElementById('create-modal').classList.remove('active');
    document.getElementById('create-form').reset();
}

function closeDetailModal() {
    document.getElementById('detail-modal').classList.remove('active');
    // 停止实时监控
    if (window.Monitoring) {
        Monitoring.stopRealtime();
    }
}

// 创建容器表单提交
document.addEventListener('DOMContentLoaded', () => {
    const createForm = document.getElementById('create-form');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const osValue = document.getElementById('create-os').value;
            const [osType, osVersion] = osValue.split(':');

            const config = {
                name: document.getElementById('create-name').value,
                cpu: parseFloat(document.getElementById('create-cpu').value),
                memory: parseInt(document.getElementById('create-memory').value),
                disk: parseInt(document.getElementById('create-disk').value),
                os_type: osType,
                os_version: osVersion,
                ssh_port: parseInt(document.getElementById('create-ssh-port').value),
                nat_start: 0,
                nat_end: 0,
                bandwidth: parseInt(document.getElementById('create-bandwidth').value)
            };

            await Containers.createContainer(config);
        });
    }
});
