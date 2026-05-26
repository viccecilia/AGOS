# Round Execution Request

## Round Identity

Round ID:
ROUND-PREDICT-003

Round Name:
AGOS_MOBILITY_DEMAND_INTENT_ENGINE

Phase:
PREDICTIVE_DEMAND_INTELLIGENCE

## 本轮目标

建立 Mobility Demand Intent Engine，让 AGOS 从知道什么时候热、哪里热，升级为知道用户到底有没有真实用车需求。

本轮把帖子、搜索、趋势、评论、问题文本分类成真实 mobility demand intent。

## 允许修改

- services/
- runtime/
- tests/
- docs/project_control_center.html
- runtime/task_results/ROUND-PREDICT-003/

## 禁止修改

- 不删除前两轮 Predictive 数据
- 不删除 Collection Gate
- 不自动触达真实用户
- 不把低可信度信号标记为高价值
- 不自动报价
- 不自动联系客户
- 不自动派单
- 不自动发布内容

## 必须运行的验证

- python -m compileall services tests
- python tests\mobility_demand_intent_smoke_test.py
- python tests\location_demand_heatmap_smoke_test.py
- python tests\seasonal_demand_calendar_smoke_test.py
- python tests\war_room_runtime_ui_smoke_test.py

## 完成定义

AGOS 获得真实用车需求识别能力，能够区分趋势噪音和真实 mobility demand。
