# ROUND-EXT-006

## Round Name

CONTROLLED_EXTERNAL_INTERACTION_GATE

## Goal

判断 AGOS 是否可以进入小范围真实外部互动试运行。

## Scope

本轮汇总 manual export pack、external evidence ledger、manual feedback intake、platform survival rulebook、external drift monitor，并生成 Controlled External Interaction Gate。

## Safety Boundary

- 不允许自动发布。
- 不允许自动回复。
- 不允许自动登录。
- 不允许平台 write API。
- 不允许自动 DM / follow / like。
- 不允许登录抓取或平台爬取。
- 只允许 human-controlled external trial。

## Required Verification

- `python -m compileall services tests`
- `python tests\controlled_external_interaction_gate_smoke_test.py`
- `python tests\war_room_runtime_ui_smoke_test.py`
- Browser verification for Control Center panel.
