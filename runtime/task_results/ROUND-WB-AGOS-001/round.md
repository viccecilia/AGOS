# ROUND-WB-AGOS-001

## Round Name

AGOS_WORKBENCH_ADAPTER_CONTRACT

## Goal

定义 Workbench 如何只读识别 AGOS 项目状态、Round 结果、Gate 和 artifacts。

## Read Scope

- `runtime/task_results/*`
- `runtime/*/*REPORT.json`
- `docs/project_control_center.html`
- `runtime/runtime_state/ui_state.json`
- `docs/runtime/runtime_state/ui_state.json`
- `services/runtime_ui_bridge.py` 输出 state

## Forbidden Scope

- Workbench 不能直接修改 AGOS 业务代码。
- Workbench 不能直接读取 secrets、API Key、OAuth Token、Refresh Token、`.env` 或 credential vault payload。
- Workbench 不能直接启动外部平台动作。
- Workbench 不能调用平台 write API。

## Required Verification

- `python -m compileall services tests`
- `python tests\agos_workbench_adapter_contract_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`
- Browser verification for Control Center panel.
