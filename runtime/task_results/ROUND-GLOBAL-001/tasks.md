# ROUND-GLOBAL-001 Tasks

## Execution Tasks

- TASK-001: Added `services/global_batch_intelligence_collection.py`.
- TASK-002: Supported CSV, JSON, RSS export, manual import, read-only API output, Google Trends-style sample, platform trend sample, and local research notes.
- TASK-003: Supported Japan, US, Europe, Korea, Taiwan, Southeast Asia, China outbound, and Global English markets.
- TASK-004: Created normalized intelligence records with required source, market, language, URL, text, topic, and safety fields.
- TASK-005: Added runtime outputs under `runtime/global_batch_intelligence_collection/`.
- TASK-006: Added Control Center panel showing record counts, distributions, source types, and safety boundaries.

## Test Tasks

- TEST-001: Added `tests/global_batch_intelligence_collection_smoke_test.py`.
- TEST-002: Verified at least 20 records, at least 5 markets, and at least 4 platforms.
- TEST-003: Verified all records are read-only and human-gated.
- TEST-004: Verified no credentials are read and no platform write API is called.

## Review Tasks

- REVIEW-001: User can see global intelligence by market, platform, language, and source type.
- REVIEW-002: User can see sample/manual/read-only boundaries.
- REVIEW-003: User can see that all records require human review.
