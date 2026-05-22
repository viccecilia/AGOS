# Round Execution Request

## Round Identity

Round ID: ROUND-SCOUT-004

Round Name: AGOS_TREND_CLUSTERING_ENGINE

Phase: SCOUT_INTELLIGENCE / AI_SCOUT_NETWORK

## 本轮目标

建立 Trend Clustering，让 AGOS 能够把不同平台、不同来源的相似问题聚成趋势。

## 本轮任务

### TASK-001

新增 `services/trend_clustering_engine.py`。

### TASK-002

聚类相似问题、相似趋势、跨平台讨论和相似情绪。

### TASK-003

建立 Trend Cluster 示例，包括东京雨天在 Reddit、TikTok、YouTube、Instagram 的跨平台聚类。

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
- `python tests\trend_clustering_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`

## 完成定义

AGOS 能够把不同平台问题聚成趋势，并在 War Room 中展示趋势聚类结果。
