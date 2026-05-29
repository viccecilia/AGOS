# ROUND-GLOBAL-002 Tasks

## Execution Tasks

- TASK-001: Added `services/global_pain_cluster_engine.py`.
- TASK-002: Read `runtime/global_batch_intelligence_collection/global_intelligence_records.json`.
- TASK-003: Clustered records by pain topic, market, platform, language, emotion, intent, season, and location.
- TASK-004: Created required pain cluster fields with source records, scores, review flags, and blocked reply/promotion flags.
- TASK-005: Added runtime outputs under `runtime/global_pain_clusters/`.
- TASK-006: Added Control Center Global Pain Clusters panel.

## Test Tasks

- TEST-001: Added `tests/global_pain_cluster_engine_smoke_test.py`.
- TEST-002: Verified Global Batch output can be read.
- TEST-003: Verified at least 5 clusters are generated.
- TEST-004: Verified every cluster has source records and scores.
- TEST-005: Verified every cluster requires human review and does not allow replies or promotion.

## Review Tasks

- REVIEW-001: User can see main global pain clusters.
- REVIEW-002: User can see cross-market and cross-platform repeated pains.
- REVIEW-003: User can see high-emotion and ranking-candidate clusters.
- REVIEW-004: User can see that this round does not generate replies or execute promotion.
