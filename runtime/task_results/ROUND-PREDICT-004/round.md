# Round Execution Request

## Round Identity

Round ID:
ROUND-PREDICT-004

Round Name:
AGOS_DEMAND_TO_ACTION_STRATEGY_ENGINE

Phase:
PREDICTIVE_DEMAND_INTELLIGENCE

## 本轮目标

建立 Demand-to-Action Strategy Engine，让 AGOS 从识别趋势和需求，升级为把趋势结果转成具体行动建议。

行动建议分为三类：平台内容行动、线下商家行动、司机/车辆运营行动。

## 允许修改

- services/
- runtime/
- tests/
- docs/project_control_center.html
- runtime/task_results/ROUND-PREDICT-004/

## 禁止修改

- 不删除 Human Gate
- 不绕过 API Collection Safety
- 不自动外部执行
- 不把建议标记成已执行
- 不自动发帖
- 不自动私信
- 不自动报价
- 不自动派单
- 不自动联系司机、商家或客户

## 必须运行的验证

- python -m compileall services tests
- python tests\demand_to_action_strategy_smoke_test.py
- python tests\mobility_demand_intent_smoke_test.py
- python tests\war_room_runtime_ui_smoke_test.py

## 完成定义

AGOS 获得趋势到行动建议能力，可以把时间趋势、空间趋势、需求趋势转成平台内容建议、线下商家建议、司机运营建议；所有行动仍需人工审核。
