# ROUND-PREDICT-002 Tasks

## 执行任务

- TASK-001: 新增 `services/location_demand_heatmap_engine.py`，建立地点维度热度结构。
- TASK-002: 新增 `runtime/location_demand_heatmap/`，输出 heatmap、signals、mobility risk、summary。
- TASK-003: 内置 Tokyo、Haneda Airport、Narita Airport、Shinjuku、Shibuya、Ueno、Osaka、Kansai Airport、Kyoto、Nagoya、Chubu Centrair Airport、Suzuka Circuit、Mount Fuji、Sapporo、Okinawa。
- TASK-004: 每个地点包含 location_id、location_name、location_type、region、related_seasons、related_events、mobility_demand_types、common_pain_points、risk scores、demand_heat_score。
- TASK-005: 读取 Seasonal Demand Calendar，生成地点-季节关系。
- TASK-006: 更新 `docs/project_control_center.html`，新增 Location Demand Heatmap 面板。

## 测试任务

- TEST-001: `tests/location_demand_heatmap_smoke_test.py`

## 协作验收任务

- REVIEW-001: 用户能看到哪些地点可能变热。
- REVIEW-002: 用户能看到为什么这些地点会热。
- REVIEW-003: 用户能看到这些地点对应什么用车需求。
