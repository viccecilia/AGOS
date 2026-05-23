# ROUND-BATCH-005

## Round Name

AGOS_RUNTIME_REPLAY_TRAINING

## Phase

RUNTIME_BATCH_INTELLIGENCE

## Goal

建立 Runtime Replay Training，让 AGOS 可以 replay 历史问题、历史回复、历史反馈、历史失败，并重新训练过去的 intelligence。

## Scope

- 新增 `services/runtime_replay_training.py`
- 建立 `runtime/replay_training/`
- 支持 historical question / reply / feedback / failure replay
- 更新 `docs/project_control_center.html` 的 Runtime Replay Training 面板

## Safety Boundary

本轮只做本地 replay training 与 JSON 归档，不自动发帖、不自动回复、不调用真实平台 write API。
