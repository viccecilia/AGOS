# ROUND-BATCH-003

## Round Name

AGOS_BATCH_HUMAN_REVIEW

## Phase

RUNTIME_BATCH_INTELLIGENCE

## Goal

建立 Batch Human Review，让 AGOS 可以对批量趋势簇进行人工批量训练。

## Scope

- 新增 `services/batch_human_review.py`
- 建立 `runtime/batch_reviews/`
- 支持批量 `approve` / `reject` / `modify` / `classify`
- 支持批量训练标签：`high_value` / `low_value` / `spam` / `dangerous` / `over_marketing`
- 更新 `docs/project_control_center.html` 的 War Room Batch Human Review 面板

## Safety Boundary

本轮只做本地训练与 JSON 归档，不自动发帖、不自动回复、不调用真实平台 write API。
