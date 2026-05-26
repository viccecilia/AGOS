# ROUND-PREDICT-002 Seasonal Trend Import Trial Tasks

## Execution Tasks
- TASK-001: Add `services/seasonal_trend_import_trial.py`.
- TASK-002: Add `runtime/seasonal_trend_import_trial/` outputs.
- TASK-003: Map trend records to Seasonal Demand Calendar entries.
- TASK-004: Produce market heatmap, keyword-season matches, demand rankings, pain point rankings, noisy signals, and human review queue items.
- TASK-005: Add Seasonal Trend Import Trial panel to `docs/project_control_center.html`.

## Test Tasks
- TEST-001: Add and run `tests\seasonal_trend_import_trial_smoke_test.py`.
- TEST-002: Run `python -m compileall services tests`.
- TEST-003: Run `python tests\seasonal_demand_calendar_smoke_test.py`.
- TEST-004: Run `python tests\war_room_runtime_ui_smoke_test.py`.

## Review Tasks
- REVIEW-001: User can see which imported keywords matched Japan tourism seasons.
- REVIEW-002: User can see market heat by season.
- REVIEW-003: User can see likely mobility demand types.
- REVIEW-004: User can see sample-only and human-review boundaries before business action.
