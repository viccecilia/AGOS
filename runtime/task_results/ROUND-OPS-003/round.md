# Round Execution Request

## Round Identity

Round ID: ROUND-OPS-003

Round Name: AGOS_REAL_FEEDBACK_CAPTURE

Phase: REAL_OPERATIONS / FEEDBACK_INTELLIGENCE

## 本轮目标

建立 Real Feedback Capture，让 AGOS 能够记录真实反馈。

## 本轮任务

### TASK-001

新增 `services/real_feedback_capture_engine.py`。

### TASK-002

记录 `liked`、`replied`、`ignored`、`saved`、`shared`。

### TASK-003

建立 Feedback Timeline。

### TASK-004

写入 `runtime/feedback_capture/`。

## 协作验收任务

用户必须能看到哪些内容真正有反馈。

## 非目标

- 不自动读取真实平台 API
- 不自动回复
- 不自动发帖
- 不把样例反馈伪装成真实平台数据

## 必须运行的验证

- `python -m compileall services tests`
- `python tests\real_feedback_capture_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`

## 完成定义

AGOS 能够记录回复反馈，并在控制中心显示 Feedback Timeline。
