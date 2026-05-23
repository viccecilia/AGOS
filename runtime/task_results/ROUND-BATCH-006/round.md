# ROUND-BATCH-006

## Round Name

AGOS_SYNTHETIC_FEEDBACK_TRAINING

## Phase

RUNTIME_BATCH_INTELLIGENCE

## Goal

建立 Synthetic Feedback Training，让 AGOS 通过模拟用户问题、反馈、互动和风险样本加速本地训练。

## Scope

- 新增 `services/synthetic_feedback_training.py`
- 建立 `runtime/synthetic_training/`
- 生成 Synthetic Training Dataset
- 更新 `docs/project_control_center.html` 的 Synthetic Feedback Training 面板

## Safety Boundary

本轮只生成本地模拟数据，不自动发帖、不自动回复、不调用真实平台 API。
