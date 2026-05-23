# ROUND-BATCH-004

## Round Name

AGOS_RUNTIME_PATTERN_LEARNING

## Phase

RUNTIME_BATCH_INTELLIGENCE

## Goal

建立 Runtime Pattern Learning，让 AGOS 从批量人工审核信号中学习问题组合到结果模式。

## Scope

- 新增 `services/runtime_pattern_learning.py`
- 建立 `runtime/pattern_memory/`
- 识别高价值、高互动、高转化、高风险模式
- 更新 `docs/project_control_center.html` 的 Runtime Pattern Learning 面板

## Safety Boundary

本轮只做本地 Pattern Memory 学习与 JSON 归档，不自动发帖、不自动回复、不调用真实平台 write API。
