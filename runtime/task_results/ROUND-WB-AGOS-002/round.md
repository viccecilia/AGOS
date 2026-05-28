# ROUND-WB-AGOS-002

## Round Name

AGOS_TRAINING_ACCEPTANCE_EXPORT

## Goal

AGOS 输出给 Workbench 的训练验收包。

## Export Content

- capability score
- replay result
- feedback evidence
- drift result
- gate status
- blocked risks

## Safety Boundary

- Workbench 可以只读 ingest 训练验收证据。
- Workbench 不能执行 AGOS 动作。
- 不导出 secrets。
- 不允许 Workbench 修改 AGOS 业务代码。
- 不允许 Workbench 启动外部平台动作或调用 write API。

## Required Verification

- `python -m compileall services tests`
- `python tests\agos_training_acceptance_export_smoke_test.py`
- `python tests\agos_workbench_adapter_contract_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`
- Browser verification for Control Center panel.
