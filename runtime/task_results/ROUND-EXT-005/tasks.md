# ROUND-EXT-005 Tasks

## Execution Tasks

- TASK-001: Add `services/external_drift_monitor.py`.
- TASK-002: Compare `expected_result` against manual feedback.
- TASK-003: Flag strategy drift, platform drift, audience drift, and tone drift.
- TASK-004: Output drift report and recommendations.
- TASK-005: Connect to `strategy_evolution` and `promotion_feedback_learning`.
- TASK-006: Add Control Center panel for External Drift Monitor.

## Test Tasks

- TEST-001: Add `tests/external_drift_monitor_smoke_test.py`.
- TEST-002: Run `python tests\strategy_evolution_smoke_test.py`.
- TEST-003: Run `python tests\promotion_feedback_learning_smoke_test.py`.

## Review Tasks

- REVIEW-001: User can see when recommendation effectiveness is declining.
- REVIEW-002: User can see strategy/platform/audience/tone drift.
- REVIEW-003: User can confirm drift only creates recommendations.
- REVIEW-004: User can confirm external execution strategy is not changed automatically.
