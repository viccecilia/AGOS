# ROUND-EXTERNAL-001 Tasks

## TASK-001
状态：done

新增 `services/external_action_sandbox.py`，建立 External Action Sandbox。

## TASK-002
状态：done

支持模拟外部回复、外部内容发布、外部趋势跟进、外部扩散动作。

## TASK-003
状态：done

所有 External Action 默认 blocked。

## TASK-004
状态：done

建立 External Action Queue，支持 `draft`、`waiting_human_approval`、`approved_for_manual_execution`、`rejected`、`cancelled`、`simulated_only` 状态枚举。本轮生成的动作全部为 `waiting_human_approval` 且 `simulated_only`。

## TASK-005
状态：done

新增 `runtime/external_action_sandbox/`。

## TASK-006
状态：done

War Room 新增 External Action Sandbox Panel。

## TASK-007
状态：done

禁止自动发帖、自动回复、自动调用 write API、自动登录、自动注册账号。

## REVIEW-001
状态：done

用户可以看到 AGOS 想做什么。

## REVIEW-002
状态：done

用户可以看到 AGOS 为什么想这样做。

## REVIEW-003
状态：done

用户可以看到为什么当前动作被 blocked。
