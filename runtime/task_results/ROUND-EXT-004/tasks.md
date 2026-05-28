# ROUND-EXT-004 Tasks

## Execution Tasks

- TASK-001: Add `services/platform_survival_rulebook.py`.
- TASK-002: Define rules for Reddit, X, TikTok, Instagram, YouTube, and Threads.
- TASK-003: Define forbidden patterns, safe CTA, posting cadence, and community risk.
- TASK-004: Connect governance to `promotion_review_center`.
- TASK-005: Connect governance to `external_action_sandbox`.
- TASK-006: Add Control Center panel for Platform Survival Rulebook.

## Test Tasks

- TEST-001: Add `tests/platform_survival_rulebook_smoke_test.py`.
- TEST-002: Run `python tests\external_action_sandbox_smoke_test.py`.
- TEST-003: Run `python tests\promotion_review_center_smoke_test.py`.

## Review Tasks

- REVIEW-001: User can see platform-specific forbidden patterns.
- REVIEW-002: User can see safe CTA and cadence rules.
- REVIEW-003: User can see high-risk actions downgraded or rejected.
- REVIEW-004: User can confirm Reddit does not default to strong marketing.
