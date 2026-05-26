# ROUND-API-COLLECT-004 Tasks

## Execution Tasks

- TASK-001: Added `services/collection_compliance_guard.py`.
- TASK-002: Added checks for rate limit, repeated queries, suspicious pattern, write API usage, and excessive polling.
- TASK-003: Blocked automated login scraping, platform-limit bypass, write API usage, and automated interaction.
- TASK-004: Added Compliance Risk Feed.
- TASK-005: Added `runtime/compliance_guard/` outputs.

## Test Tasks

- TEST-001: Added `python tests\collection_compliance_guard_smoke_test.py`.

## Review Tasks

- User can see compliance risk feed and confirm collection remains read-only and safe.
