# ROUND-WB-AGOS-003 Tasks

## Execution Tasks

- [x] 新增 read-only training data manifest 服务。
- [x] 输出 training dataset manifest。
- [x] 输出 training data access policy。
- [x] 输出 training data audit review。
- [x] 输出 manifest summary。
- [x] 排除 credentials / secrets / token / OAuth / refresh 相关路径。
- [x] 接入 Runtime UI Bridge。
- [x] 接入 Control Center HTML。

## Test Tasks

- [x] 新增 `tests\agos_read_only_training_data_manifest_smoke_test.py`。
- [x] 运行 `python -m compileall services tests`。
- [x] 运行 `python tests\agos_read_only_training_data_manifest_smoke_test.py`。
- [x] 运行 `python tests\agos_training_acceptance_export_smoke_test.py`。
- [x] 运行 `python tests\war_room_runtime_ui_smoke_test.py`。
- [x] 浏览器验证 Read-Only Training Data Manifest 面板。

## Review Tasks

- [x] 用户可以看到 sample-first。
- [x] 用户可以看到 read-only。
- [x] 用户可以看到 audit-first。
- [x] 用户可以看到 human-gated。
- [x] 用户可以看到 contains_credentials=false。
- [x] 用户可以确认 Workbench may read=true，may write=false，may execute=false。
