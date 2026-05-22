# Round Execution Request

## Round Identity

Round ID: ROUND-OPS-001

Round Name: AGOS_DAILY_QUESTION_IMPORT

Phase: REAL_OPERATIONS / FEEDBACK_INTELLIGENCE

## 本轮目标

让 AGOS 从 Scout Intelligence 升级到 Daily Real Operations，每天真正导入问题。

## 本轮任务

### TASK-001

新增 `services/daily_question_import_engine.py`。

### TASK-002

支持 RSS、手动导入、CSV、JSON、本地文本。

### TASK-003

每天导入 10-30 条问题。

### TASK-004

写入 `runtime/daily_question_import/`。

## 协作验收任务

用户必须能看到今天真正导入了哪些问题。

## 非目标

- 不抓取登录数据
- 不自动回复
- 不自动发布
- 不访问真实平台 API
- 不把样例导入伪装成外部平台抓取

## 必须运行的验证

- `python -m compileall services tests`
- `python tests\daily_question_import_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`

## 完成定义

AGOS 能够每日导入问题，并在控制中心显示当天导入批次。
