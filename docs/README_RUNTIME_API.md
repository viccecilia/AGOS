# AGOS Local Runtime API

本地 Runtime API 只用于 JAG-LAB 训练沙盒，绑定 `127.0.0.1:8766`，不会开放公网，也不会调用真实社交平台 API。

## 启动方式

```powershell
cd C:\PycharmProjects\AGOS

python services\runtime_api_server.py
```

另开一个终端启动控制中心页面：

```powershell
python -m http.server 8765 --directory docs
```

访问：

```text
http://127.0.0.1:8765/project_control_center.html?runtime_ui=1#war-room-growth
```

## API

- `GET /api/runtime/status`
- `POST /api/runtime/start`
- `POST /api/runtime/stop`
- `POST /api/runtime/correction`
- `POST /api/runtime/review`

## 安全边界

禁止：

- 自动发帖
- 自动回复真实用户
- 自动注册账号
- 自动登录社交平台
- 访问公网平台 API
- 绕过平台限制

当前所有行为限定为：

- 本地 JAG-LAB Runtime Training
- 本地 JSON
- 本地日志
- 本地 Review Gate
- 本地 Memory Deposit
