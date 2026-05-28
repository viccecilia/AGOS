# ROUND-WB-AGOS-001 Tasks

## Execution Tasks

- [x] 新增 Workbench read-only adapter contract 服务。
- [x] 建立 task results 索引。
- [x] 建立 runtime report 索引。
- [x] 建立 gate index。
- [x] 建立 safety review，明确 forbidden operations。
- [x] 接入 Runtime UI Bridge。
- [x] 接入 Control Center HTML。

## Test Tasks

- [x] 新增 `tests\agos_workbench_adapter_contract_smoke_test.py`。
- [x] 运行 `python -m compileall services tests`。
- [x] 运行 `python tests\agos_workbench_adapter_contract_smoke_test.py`。
- [x] 运行 `python tests\war_room_runtime_ui_smoke_test.py`。
- [x] 浏览器验证 Workbench Adapter Contract 面板。

## Review Tasks

- [x] 用户可以看到 Workbench 只能 read-only。
- [x] 用户可以看到 Workbench 可读 task results、runtime reports、gates、Control Center 和 runtime UI state。
- [x] 用户可以看到 Workbench 不能修改业务代码。
- [x] 用户可以看到 Workbench 不能读取 secrets。
- [x] 用户可以看到 Workbench 不能启动外部平台动作。
