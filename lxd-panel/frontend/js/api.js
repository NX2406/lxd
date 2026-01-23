// API客户端封装
const API_BASE_URL = window.location.origin + '/api';

class APIClient {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    }

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

            if (response.status === 401) {
                this.clearToken();
                window.location.reload();
                throw new Error('未授权，请重新登录');
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '请求失败');
            }

            return await response.json();
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // 认证相关
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '登录失败');
        }

        return await response.json();
    }

    async logout() {
        try {
            await this.post('/auth/logout');
        } finally {
            this.clearToken();
        }
    }

    async getCurrentUser() {
        return this.get('/auth/me');
    }

    // 容器管理相关
    async listContainers() {
        return this.get('/containers');
    }

    async getContainer(name) {
        return this.get(`/containers/${name}`);
    }

    async createContainer(config) {
        return this.post('/containers', config);
    }

    async startContainer(name) {
        return this.post(`/containers/${name}/start`);
    }

    async stopContainer(name) {
        return this.post(`/containers/${name}/stop`);
    }

    async restartContainer(name) {
        return this.post(`/containers/${name}/restart`);
    }

    async rebuildContainer(name, osType, osVersion) {
        return this.post(`/containers/${name}/rebuild`, {
            os_type: osType,
            os_version: osVersion
        });
    }

    async deleteContainer(name) {
        return this.delete(`/containers/${name}`);
    }

    // 监控相关
    async getCurrentStats(name) {
        return this.get(`/monitoring/${name}/current`);
    }

    async getHistoryStats(name, hours = 24) {
        return this.get(`/monitoring/${name}/history?hours=${hours}`);
    }

    // VNC相关
    async getVNCToken(name) {
        return this.get(`/vnc/${name}/token`);
    }
}

// 全局API客户端实例
const api = new APIClient();
