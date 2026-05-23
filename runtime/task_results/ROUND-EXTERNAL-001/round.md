# ROUND-EXTERNAL-001

## Round Name
AGOS_EXTERNAL_ACTION_SANDBOX

## Phase
CONTROLLED_EXTERNAL_OPERATIONS_PREPARATION

## Goal
建立 External Action Sandbox，让 AGOS 开始准备受控外部动作，但不真正自动执行。

## Scope
- 新增 `services/external_action_sandbox.py`
- 输出 `runtime/external_action_sandbox/`
- 在 War Room 控制中心显示 External Action Sandbox Panel
- 所有外部动作默认 blocked，并进入 Human Gate

## Safety Boundary
本轮不实现自动发帖、自动回复、自动 follow、自动 DM、自动点赞、自动登录、自动注册账号，也不调用真实平台 write API。
