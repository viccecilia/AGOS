# Round Execution Request

## Round Identity

Round ID:
ROUND-PREDICT-002

Round Name:
AGOS_LOCATION_DEMAND_HEATMAP_ENGINE

Phase:
PREDICTIVE_DEMAND_INTELLIGENCE

## 本轮目标

建立 Location Demand Heatmap Engine，让 AGOS 从只知道什么时候可能热，升级为知道哪里可能热。

本轮建立日本城市、机场、车站、景点、商圈、酒店区、展会中心、体育场馆、赛车 / 演唱会 / 发布会场地的人流和用车热度地图。

## 允许修改

- services/
- runtime/
- tests/
- docs/project_control_center.html
- runtime/task_results/ROUND-PREDICT-002/

## 禁止修改

- 不删除 Seasonal Calendar
- 不删除 API Collection Gate
- 不绕过 Human Review
- 不把样本地点标记成真实实时人流
- 不做实时 GPS 调度
- 不自动联系车辆
- 不自动报价
- 不自动发布外部内容

## 必须运行的验证

- python -m compileall services tests
- python tests\location_demand_heatmap_smoke_test.py
- python tests\seasonal_demand_calendar_smoke_test.py
- python tests\war_room_runtime_ui_smoke_test.py

## 完成定义

AGOS 获得空间维度需求热力图，能够判断日本哪些地点可能出现用车需求高峰。
