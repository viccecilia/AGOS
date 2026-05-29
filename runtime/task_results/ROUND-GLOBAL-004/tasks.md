# ROUND-GLOBAL-004 Tasks

## Execution Tasks

- TASK-001: Added `services/market_intelligence_matrix.py`.
- TASK-002: Read global intelligence records, global pain clusters, and platform pain profiles.
- TASK-003: Supported Japan, US, Europe, Korea, Taiwan, Southeast Asia, and China outbound.
- TASK-004: Generated market profiles with languages, dominant pain, travel style, mobility need, trust barrier, price sensitivity, platform preference, content tone, conversion risk, and opportunity score.
- TASK-005: Added runtime outputs under `runtime/market_intelligence_matrix/`.
- TASK-006: Added Control Center Market Intelligence Matrix panel.

## Test Tasks

- TEST-001: Added `tests/market_intelligence_matrix_smoke_test.py`.
- TEST-002: Verified at least 5 markets are covered.
- TEST-003: Verified every market has platform preference and opportunity score.
- TEST-004: Verified China outbound does not pollute Japan local.
- TEST-005: Verified no automatic promotion, replies, or write API.

## Review Tasks

- REVIEW-001: User can see pain differences by market.
- REVIEW-002: User can see market platform preference.
- REVIEW-003: User can see conversion risk and opportunity score.
- REVIEW-004: User can see market isolation boundaries.
