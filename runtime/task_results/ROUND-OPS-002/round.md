# Round Execution Request

## Round Identity

Round ID: ROUND-OPS-002

Round Name: AGOS_REAL_REPLY_ATTEMPTS

Phase: REAL_OPERATIONS / FEEDBACK_INTELLIGENCE

## 本轮目标

让 AGOS 开始真实回复尝试，但所有回复都必须先进入人工审核。

## 本轮任务

### TASK-001

新增 `services/real_reply_attempt_engine.py`。

### TASK-002

生成 Reddit 回复、TikTok 评论草稿、X 回复草稿。

### TASK-003

所有回复进入 `needs_human_review`。

### TASK-004

记录 `approved`、`rejected`、`modified`。

## 协作验收任务

用户必须能审核真实回复。

## 非目标

- 不自动回复
- 不自动发帖
- 不访问真实平台 API
- 不登录或注册平台账号

## 必须运行的验证

- `python -m compileall services tests`
- `python tests\real_reply_attempts_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`

## 完成定义

AGOS 能够生成真实回复草稿，并把所有草稿放入人工审核队列。
