# ROUND-PREDICT-005 Tasks

## Execution Tasks
- TASK-001: Add `services/predictive_demand_gate.py`.
- TASK-002: Validate Seasonal Demand Calendar, Location Demand Heatmap, Mobility Demand Intent, and Demand-to-Action Strategy.
- TASK-003: Output Predictive Demand Report with readiness, high-value seasons, high-value locations, high-value mobility intents, recommended actions, risk review, and next phase recommendation.
- TASK-004: Output Demand Intelligence Safety Review for sample data, prediction boundary, noise risk, automation flags, and human review requirement.
- TASK-005: Persist `runtime/predictive_demand_gate/` artifacts.
- TASK-006: Update `docs/project_control_center.html` with Predictive Demand Gate status.

## Test Tasks
- TEST-001: Run `python -m compileall services tests`.
- TEST-002: Run `python tests\predictive_demand_gate_smoke_test.py`.
- TEST-003: Run `python tests\demand_to_action_strategy_smoke_test.py`.
- TEST-004: Run `python tests\war_room_runtime_ui_smoke_test.py`.
- TEST-005: Validate embedded project-state JSON and browser-visible control center panel.

## Review Tasks
- REVIEW-001: User can confirm whether AGOS can predict when demand may heat up.
- REVIEW-002: User can confirm whether AGOS can predict where demand may heat up.
- REVIEW-003: User can confirm whether AGOS can identify which mobility demand may heat up.
- REVIEW-004: User can confirm whether AGOS can generate action recommendations.
- REVIEW-005: User can confirm all actions still require human review and will not execute automatically.
