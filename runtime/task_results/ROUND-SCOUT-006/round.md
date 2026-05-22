# Round Execution Request

## Round Identity

Round ID: ROUND-SCOUT-006

Round Name: AGOS_STRATEGIC_INTERPRETATION_ENGINE

Phase: SCOUT_INTELLIGENCE / AI_SCOUT_NETWORK

## 本轮目标

建立 Strategic Interpretation，让 AGOS 能够解释趋势背后的意义。

## 本轮任务

### TASK-001

新增 `services/strategic_interpretation_engine.py`。

### TASK-002

AGOS 必须解释为什么这个趋势重要。

### TASK-003

输出风险、机会、内容方向、回复方向和平台方向。

### TASK-004

新增 Strategic Feed。

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
- `python tests\strategic_interpretation_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`

## 完成定义

AGOS 能够解释趋势背后的意义，并在 War Room 中显示 Strategic Feed。
