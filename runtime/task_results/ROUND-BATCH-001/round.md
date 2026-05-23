# ROUND-BATCH-001

## Round Name
AGOS_BATCH_SCOUT_RUNTIME

## Phase
RUNTIME_BATCH_INTELLIGENCE

## Goal
让 AGOS 从单问题 Runtime 升级为 Batch Scout Runtime。

## Scope
- 新增 `services/batch_scout_runtime.py`
- 支持一次处理 50-500 个问题
- 支持批量 Scout、Analyze、Classify、Priority Ranking
- 输出 `runtime/batch_runtime/`
- 在 War Room 控制中心显示 Batch Scout Runtime Panel

## Safety Boundary
本轮只处理本地问题文本，不自动发帖、回复、follow、DM，不调用任何外部 write API。
