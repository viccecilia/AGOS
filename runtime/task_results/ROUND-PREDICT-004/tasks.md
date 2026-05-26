# ROUND-PREDICT-004 Tasks

## 执行任务

- TASK-001: 新增 `services/demand_to_action_strategy_engine.py`，建立趋势到行动建议策略引擎。
- TASK-002: 输入 Seasonal Demand Calendar、Location Demand Heatmap、Mobility Demand Intent、Live Memory Import、Collection Review & Correction。
- TASK-003: 输出平台内容策略，包括 Reddit、TikTok、X、YouTube、Instagram、小红书、SEO。
- TASK-004: 输出线下商家策略，覆盖包车公司、机场接送公司、旅行社、酒店、地接社、展会服务商、活动主办方。
- TASK-005: 输出司机/车辆运营策略，包括待命区域、重点时间段、车型、语言准备、行李空间、等待风险、服务话术。
- TASK-006: 新增 `runtime/demand_to_action_strategy/` 输出结果文件。
- TASK-007: 所有 action 默认 `needs_human_review`，禁止自动发布、自动联系、自动派单。
- TASK-008: 更新 `docs/project_control_center.html`，新增 Demand-to-Action Strategy 面板。

## 测试任务

- TEST-001: `tests/demand_to_action_strategy_smoke_test.py`

## 协作验收任务

- REVIEW-001: 用户能看到平台应该发什么内容。
- REVIEW-002: 用户能看到线下公司应该准备什么。
- REVIEW-003: 用户能看到司机和车辆应该怎么准备。
- REVIEW-004: 用户能看到所有行动都需要人工审核。
