# Round Execution Request

## Round Identity

Round ID: ROUND-SCOUT-007

Round Name: AGOS_CROSS_PLATFORM_EXPANSION

Phase: SCOUT_INTELLIGENCE / AI_SCOUT_NETWORK

## 本轮目标

建立 Cross Platform Expansion，让 AGOS 能够跨平台扩散增长机会。

## 本轮任务

### TASK-001

新增 `services/cross_platform_expansion_engine.py`。

### TASK-002

支持 TikTok 热点扩展到 Reddit、YouTube、Instagram、X、SEO。

### TASK-003

建立 Expansion Strategy。

### TASK-004

输出 `runtime/cross_platform_expansion/`。

## 非目标

- 不接入真实平台 API
- 不自动发帖
- 不自动回复
- 不自动登录或注册账号
- 不绕过平台限制

## 允许修改

- `services/`
- `runtime/`
- `tests/`
- `docs/project_control_center.html`

## 禁止修改

- 不删除 60 Round
- 不删除 phaseBlueprint
- 不删除 realGrowthVerification
- 不启用外部平台自动化

## 必须运行的验证

- `python -m compileall services tests`
- `python tests\cross_platform_expansion_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`

## 完成定义

AGOS 能够跨平台扩散增长机会，并在 War Room 中显示 Cross Platform Expansion。
