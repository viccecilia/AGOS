# ROUND-EXT-002 Tasks

## Execution Tasks

- TASK-001: Defined evidence ledger schema.
- TASK-002: Supported manual publish time, platform, URL, screenshot path, executor, and risk notes.
- TASK-003: Supported statuses: planned, manually_executed, evidence_pending, rejected.
- TASK-004: Blocked feedback learning unless manual execution has human evidence.
- TASK-005: Added runtime outputs.
- TASK-006: Added Control Center panel.

## Test Tasks

- TEST-001: Added `tests/external_evidence_ledger_smoke_test.py`.

## Collaboration Review Tasks

- REVIEW-001: User can see which manual exports have evidence.
- REVIEW-002: User can see which records are blocked from feedback learning.
- REVIEW-003: User can confirm AGOS does not crawl or auto-verify external pages.
