# ROUND-PREDICT-003 Tasks

## 执行任务

- TASK-001: 新增 `services/mobility_demand_intent_engine.py`，建立用车需求意图分类。
- TASK-002: 支持 airport_transfer、private_charter、family_trip、elderly_support、luggage_heavy_trip、night_arrival、multi_city_transfer、event_pickup、station_to_hotel、sightseeing_route、price_comparison、public_transport_anxiety、no_real_mobility_intent。
- TASK-003: 支持 normalized live data、question inbox、scout intelligence、Google Trends keyword signal、local CSV、local JSON、manual import。
- TASK-004: 每条 intent 输出完整 intent 字段、评分和 recommended_route。
- TASK-005: 建立低价值过滤，识别闲聊、看热闹、无旅行计划、无交通需求、低可信趋势和无关信号。
- TASK-006: 新增 `runtime/mobility_demand_intent/` 输出结果文件。
- TASK-007: 更新 `docs/project_control_center.html`，新增 Mobility Demand Intent 面板。

## 测试任务

- TEST-001: `tests/mobility_demand_intent_smoke_test.py`

## 协作验收任务

- REVIEW-001: 用户能看到哪些数据是真正有用车需求。
- REVIEW-002: 用户能看到哪些数据只是噪音。
- REVIEW-003: 用户能看到每类需求应该进入什么运营路径。
