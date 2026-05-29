# ROUND-GLOBAL-012 Tasks

## Execution Tasks
- TASK-001: Done. Added `services/cross_dimensional_correlation.py`.
- TASK-002: Done. Reads seasonal intelligence, spatial intelligence, event intelligence, mobility intelligence, demand prediction, platform pain intelligence, and market intelligence matrix.
- TASK-003: Done. Correlates season + location + event + platform + market + pain + mobility demand.
- TASK-004: Done. Each chain includes required identity, evidence, confidence, strategy type, and human-review fields.
- TASK-005: Done. Added runtime outputs under `runtime/cross_dimensional_correlation/`.
- TASK-006: Done. Added Cross-Dimensional Correlation panel to the Control Center.

## Test Tasks
- TEST-001: Done. Added `tests/cross_dimensional_correlation_smoke_test.py`.

## Review Tasks
- REVIEW-001: Done. Control Center shows why AGOS expects a demand signal.
- REVIEW-002: Done. Control Center shows season, location, event, platform, market, pain, and mobility evidence.
- REVIEW-003: Done. Control Center shows evidence sources and confidence.
- REVIEW-004: Done. Control Center shows next strategy type.
- REVIEW-005: Done. Control Center shows publish, contact, dispatch, quote, and write API remain blocked.
