// 监控模块
const Monitoring = {
    charts: {},
    websocket: null,
    updateInterval: null,

    // 加载图表
    async loadCharts(containerName) {
        try {
            const history = await api.getHistoryStats(containerName, 24);

            // 准备数据
            const labels = history.map(d => new Date(d.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
            const cpuData = history.map(d => d.cpu_usage || 0);
            const memoryData = history.map(d => d.memory_percent || 0);
            const networkRxData = history.map(d => d.network_rx_rate || 0);
            const networkTxData = history.map(d => d.network_tx_rate || 0);
            const diskData = history.map(d => d.disk_percent || 0);

            // CPU图表
            this.createChart('cpu-chart', 'CPU使用率 (%)', labels, [{
                label: 'CPU',
                data: cpuData,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }]);

            // 内存图表
            this.createChart('memory-chart', '内存使用率 (%)', labels, [{
                label: '内存',
                data: memoryData,
                borderColor: '#48bb78',
                backgroundColor: 'rgba(72, 187, 120, 0.1)',
                tension: 0.4
            }]);

            // 网络图表
            this.createChart('network-chart', '网络速率 (KB/s)', labels, [
                {
                    label: '接收',
                    data: networkRxData,
                    borderColor: '#4299e1',
                    backgroundColor: 'rgba(66, 153, 225, 0.1)',
                    tension: 0.4
                },
                {
                    label: '发送',
                    data: networkTxData,
                    borderColor: '#ecc94b',
                    backgroundColor: 'rgba(236, 201, 75, 0.1)',
                    tension: 0.4
                }
            ]);

            // 磁盘图表
            this.createChart('disk-chart', '磁盘使用率 (%)', labels, [{
                label: '磁盘',
                data: diskData,
                borderColor: '#4fd1c5',
                backgroundColor: 'rgba(79, 209, 197, 0.1)',
                tension: 0.4
            }]);

        } catch (error) {
            console.error('加载图表失败:', error);
        }
    },

    // 创建图表
    createChart(canvasId, label, labels, datasets) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // 销毁旧图表
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        // 创建新图表
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#a0aec0'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a0aec0'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a0aec0',
                            maxTicksLimit: 10
                        }
                    }
                }
            }
        });
    },

    // 启动实时监控
    startRealtime(containerName) {
        this.stopRealtime();

        // 使用轮询而不是WebSocket (更稳定)
        this.updateInterval = setInterval(async () => {
            try {
                const stats = await api.getCurrentStats(containerName);
                if (stats) {
                    this.updateCharts(stats);
                }
            } catch (error) {
                console.error('更新监控数据失败:', error);
            }
        }, 5000);  // 每5秒更新一次
    },

    // 停止实时监控
    stopRealtime() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    },

    // 更新图表数据
    updateCharts(stats) {
        // 更新CPU图表
        if (this.charts['cpu-chart']) {
            this.addDataPoint(this.charts['cpu-chart'], stats.cpu_usage || 0);
        }

        // 更新内存图表
        if (this.charts['memory-chart']) {
            this.addDataPoint(this.charts['memory-chart'], stats.memory?.percent || 0);
        }

        // 更新网络图表
        if (this.charts['network-chart']) {
            const chart = this.charts['network-chart'];
            const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

            chart.data.labels.push(time);
            chart.data.datasets[0].data.push(stats.network?.rx_rate || 0);
            chart.data.datasets[1].data.push(stats.network?.tx_rate || 0);

            // 保持最多50个数据点
            if (chart.data.labels.length > 50) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
                chart.data.datasets[1].data.shift();
            }

            chart.update('none');
        }

        // 更新磁盘图表
        if (this.charts['disk-chart']) {
            this.addDataPoint(this.charts['disk-chart'], stats.disk?.percent || 0);
        }
    },

    // 添加数据点
    addDataPoint(chart, value) {
        const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

        chart.data.labels.push(time);
        chart.data.datasets[0].data.push(value);

        // 保持最多50个数据点
        if (chart.data.labels.length > 50) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        chart.update('none');
    }
};
