# ROUND-EXT-006 Tasks

## Execution Tasks

- [x] 汇总 manual promotion export pack。
- [x] 汇总 external evidence ledger。
- [x] 汇总 manual external feedback intake。
- [x] 汇总 platform survival rulebook。
- [x] 汇总 external drift monitor。
- [x] 生成 Controlled External Interaction Gate report。
- [x] 明确 allowed / blocked / review_required actions。
- [x] 接入 Runtime UI Bridge。
- [x] 接入 Control Center HTML。

## Test Tasks

- [x] 新增 `tests\controlled_external_interaction_gate_smoke_test.py`。
- [x] 运行 `python -m compileall services tests`。
- [x] 运行 `python tests\controlled_external_interaction_gate_smoke_test.py`。
- [x] 运行 `python tests\war_room_runtime_ui_smoke_test.py`。
- [x] 浏览器验证 Gate 面板可见且安全边界正确。

## Review Tasks

- [x] 用户可以看到 Gate decision。
- [x] 用户可以看到 allowed / review_required / blocked actions。
- [x] 用户可以看到自动发布、自动回复、自动登录、平台写 API 均为 false。
- [x] 用户可以确认当前只允许 human-controlled external trial。
