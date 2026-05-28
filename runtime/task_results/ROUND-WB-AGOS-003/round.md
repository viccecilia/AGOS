# ROUND-WB-AGOS-003

## Round Name

AGOS_READ_ONLY_TRAINING_DATA_MANIFEST

## Goal

给 Workbench 提供只读训练数据 manifest。

## Principles

- sample-first
- read-only
- audit-first
- human-gated
- 不包含 credentials

## Safety Boundary

- Workbench 可以读取训练数据 manifest。
- Workbench 不能写入 AGOS。
- Workbench 不能执行 AGOS 动作。
- 不导出 credentials、tokens、OAuth、refresh token、`.env` 或 secrets。
- 不允许平台 write API。

## Required Verification

- `python -m compileall services tests`
- `python tests\agos_read_only_training_data_manifest_smoke_test.py`
- `python tests\agos_training_acceptance_export_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`
- Browser verification for Control Center panel.
