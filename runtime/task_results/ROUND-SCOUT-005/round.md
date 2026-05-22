# Round Execution Request

## Round Identity

Round ID: ROUND-SCOUT-005

Round Name: AGOS_HEAT_DETECTION_ENGINE

Phase: SCOUT_INTELLIGENCE / AI_SCOUT_NETWORK

## 本轮目标

建立 Heat Detection，让 AGOS 能够发现什么正在变热。

## 本轮任务

### TASK-001

新增 `services/heat_detection_engine.py`。

### TASK-002

检测上涨趋势、高互动趋势、高情绪趋势和高传播趋势。

### TASK-003

建立 Opportunity Ranking。

### TASK-004

输出 `runtime/heat_signals/`。

## 非目标

- 不接入真实平台 API
- 不自动发帖
- 不自动回复
- 不抓取登录数据
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
- `python tests\heat_detection_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`

## 完成定义

AGOS 能够发现什么正在变热，并在 War Room 中显示 Heat Detection 和 Opportunity Ranking。
