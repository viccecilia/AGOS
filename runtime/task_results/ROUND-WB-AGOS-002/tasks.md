# ROUND-WB-AGOS-002 Tasks

## Execution Tasks

- [x] 新增训练验收包服务。
- [x] 汇总 capability score。
- [x] 汇总 replay result。
- [x] 汇总 feedback evidence。
- [x] 汇总 drift result。
- [x] 汇总 gate status。
- [x] 汇总 blocked risks。
- [x] 接入 Runtime UI Bridge。
- [x] 接入 Control Center HTML。

## Test Tasks

- [x] 新增 `tests\agos_training_acceptance_export_smoke_test.py`。
- [x] 运行 `python -m compileall services tests`。
- [x] 运行 `python tests\agos_training_acceptance_export_smoke_test.py`。
- [x] 运行 `python tests\agos_workbench_adapter_contract_smoke_test.py`。
- [x] 运行 `python tests\war_room_runtime_ui_smoke_test.py`。
- [x] 浏览器验证 Training Acceptance Export 面板。

## Review Tasks

- [x] 用户可以看到 capability score。
- [x] 用户可以看到 replay result。
- [x] 用户可以看到 feedback evidence。
- [x] 用户可以看到 drift result。
- [x] 用户可以看到 gate status。
- [x] 用户可以看到 blocked risks。
- [x] 用户可以确认 Workbench may ingest=true，但 may execute=false。
