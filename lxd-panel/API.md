# LXD管理面板 API文档

本文档详细说明了LXD管理面板的所有API接口，便于集成和扩展开发。

## 基础信息

- **基础URL**: `http://您的服务器:8000`
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: API Key (可选，预留扩展)

## API端点列表

### 1. 系统信息

#### 1.1 根路径
```
GET /
```

**响应示例**:
```json
{
  "name": "LXD管理面板API",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2026-01-23T11:30:00"
}
```

#### 1.2 健康检查
```
GET /api/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "lxd_connected": true
}
```

#### 1.3 宿主机信息
```
GET /api/host/info
```

**响应示例**:
```json
{
  "cpu_cores": 4,
  "cpu_percent": 35.2,
  "memory_total": 16384,
  "memory_used": 8192,
  "memory_percent": 50.0,
  "disk_total": 500,
  "disk_used": 250,
  "disk_percent": 50.0
}
```

---

### 2. 实例管理

#### 2.1 获取所有实例
```
GET /api/instances
```

**响应示例**:
```json
[
  {
    "name": "test1",
    "status": "Running",
    "ipv4": "10.0.0.100",
    "ipv6": null,
    "architecture": "x86_64",
    "created_at": "2026-01-20T10:00:00",
    "description": "test1 20001 password123 30000 30025"
  }
]
```

#### 2.2 获取实例详情
```
GET /api/instances/{name}
```

**路径参数**:
- `name`: 实例名称

**响应示例**:
```json
{
  "info": {
    "name": "test1",
    "status": "Running",
    "ipv4": "10.0.0.100",
    "ipv6": null,
    "architecture": "x86_64",
    "created_at": "2026-01-20T10:00:00",
    "description": "test1 20001 password123 30000 30025"
  },
  "resources": {
    "cpu_percent": 47.5,
    "memory_used": 256,
    "memory_total": 512,
    "disk_used": 2048,
    "disk_total": 10240,
    "network_rx": 100,
    "network_tx": 50
  },
  "ssh_port": 20001,
  "nat_ports": "30000-30025",
  "root_password": "password123"
}
```

#### 2.3 获取实例资源使用
```
GET /api/instances/{name}/resources
```

**路径参数**:
- `name`: 实例名称

**响应示例**:
```json
{
  "cpu_percent": 47.5,
  "memory_used": 256,
  "memory_total": 512,
  "disk_used": 2048,
  "disk_total": 10240,
  "network_rx": 100,
  "network_tx": 50
}
```

---

### 3. 实例操作

#### 3.1 启动实例
```
POST /api/instances/{name}/start
```

**路径参数**:
- `name`: 实例名称

**响应示例**:
```json
{
  "success": true,
  "message": "实例 test1 启动成功",
  "data": null
}
```

#### 3.2 停止实例
```
POST /api/instances/{name}/stop
```

**路径参数**:
- `name`: 实例名称

**响应示例**:
```json
{
  "success": true,
  "message": "实例 test1 停止成功",
  "data": null
}
```

#### 3.3 重启实例
```
POST /api/instances/{name}/restart
```

**路径参数**:
- `name`: 实例名称

**响应示例**:
```json
{
  "success": true,
  "message": "实例 test1 重启成功",
  "data": null
}
```

#### 3.4 删除实例
```
DELETE /api/instances/{name}?force=false
```

**路径参数**:
- `name`: 实例名称

**查询参数**:
- `force`: 是否强制删除（停止后删除），默认false

**响应示例**:
```json
{
  "success": true,
  "message": "实例 test1 删除成功",
  "data": null
}
```

---

### 4. WebSocket实时监控

#### 4.1 实时监控连接
```
WS /ws/monitor
```

**连接示例** (JavaScript):
```javascript
const ws = new WebSocket('ws://服务器IP:8000/ws/monitor');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**消息格式**:
```json
{
  "type": "update",
  "timestamp": "2026-01-23T11:30:00",
  "data": {
    "instances": [
      {
        "name": "test1",
        "status": "Running",
        "ipv4": "10.0.0.100",
        "resources": {
          "cpu_percent": 47.5,
          "memory_used": 256,
          "memory_total": 512,
          "disk_used": 2048,
          "disk_total": 10240,
          "network_rx": 100,
          "network_tx": 50
        },
        "ssh_port": 20001,
        "nat_ports": "30000-30025"
      }
    ],
    "host": {
      "cpu_cores": 4,
      "cpu_percent": 35.2,
      "memory_total": 16384,
      "memory_used": 8192,
      "memory_percent": 50.0,
      "disk_total": 500,
      "disk_used": 250,
      "disk_percent": 50.0
    }
  }
}
```

**推送频率**: 每5秒推送一次

---

## 数据模型

### InstanceInfo (实例基本信息)
```typescript
{
  name: string;           // 实例名称
  status: string;         // 状态: Running, Stopped等
  ipv4: string | null;    // IPv4地址
  ipv6: string | null;    // IPv6地址
  architecture: string;   // 架构: x86_64, aarch64等
  created_at: datetime;   // 创建时间
  description: string;    // 描述信息
}
```

### ResourceUsage (资源使用)
```typescript
{
  cpu_percent: float;     // CPU使用率 (0-100)
  memory_used: int;       // 已用内存 (MB)
  memory_total: int;      // 总内存 (MB)
  disk_used: int;         // 已用磁盘 (MB)
  disk_total: int;        // 总磁盘 (MB)
  network_rx: int;        // 接收流量 (MB)
  network_tx: int;        // 发送流量 (MB)
}
```

### InstanceDetail (实例详情)
```typescript
{
  info: InstanceInfo;
  resources: ResourceUsage;
  ssh_port: int | null;     // SSH端口
  nat_ports: string | null; // NAT端口范围
  root_password: string | null; // Root密码
}
```

---

## 错误处理

### 错误响应格式
```json
{
  "detail": "错误描述信息"
}
```

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 常见错误

#### 实例不存在
```json
{
  "detail": "实例 test1 不存在"
}
```

#### LXD连接失败
```json
{
  "detail": "LXD服务不可用"
}
```

---

## 扩展开发指南

### 添加新的API端点

在 `backend/app.py` 中添加:

```python
@app.get("/api/custom/endpoint", tags=["自定义"])
async def custom_endpoint():
    """自定义端点说明"""
    try:
        # 你的业务逻辑
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 添加新的LXD操作

在 `backend/lxd_manager.py` 中添加:

```python
def custom_operation(self, name: str) -> bool:
    """自定义操作"""
    try:
        container = self.client.containers.get(name)
        # 执行操作
        return True
    except Exception as e:
        print(f"操作失败: {e}")
        return False
```

### WebSocket消息扩展

修改 `backend/app.py` 中的WebSocket端点:

```python
@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 添加自定义数据
            custom_data = get_custom_data()
            
            await websocket.send_json({
                "type": "update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "instances": instances_data,
                    "custom": custom_data  # 新增字段
                }
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## 测试示例

### cURL测试

```bash
# 获取所有实例
curl http://localhost:8000/api/instances

# 获取实例详情
curl http://localhost:8000/api/instances/test1

# 启动实例
curl -X POST http://localhost:8000/api/instances/test1/start

# 停止实例
curl -X POST http://localhost:8000/api/instances/test1/stop

# 删除实例
curl -X DELETE "http://localhost:8000/api/instances/test1?force=true"
```

### Python测试

```python
import requests

BASE_URL = "http://localhost:8000"

# 获取实例列表
response = requests.get(f"{BASE_URL}/api/instances")
instances = response.json()
print(instances)

# 启动实例
response = requests.post(f"{BASE_URL}/api/instances/test1/start")
result = response.json()
print(result)
```

### JavaScript测试

```javascript
const BASE_URL = 'http://localhost:8000';

// 获取实例列表
fetch(`${BASE_URL}/api/instances`)
  .then(res => res.json())
  .then(data => console.log(data));

// 启动实例
fetch(`${BASE_URL}/api/instances/test1/start`, {
  method: 'POST'
})
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## 版本历史

### v1.0.0 (2026-01-23)
- ✨ 初始API版本
- 📊 实例管理基础功能
- 🔄 WebSocket实时监控
- 📡 宿主机信息查询

---

## 技术支持

如有API相关问题，请参考：
- README.md - 基础使用说明
- 后端代码注释
- 提交Issue反馈

## 许可证

MIT License
