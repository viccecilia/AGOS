# ROUND-GLOBAL-005 Tasks

## Execution Tasks

- TASK-001: Added `services/cross_platform_correlation_expansion.py`.
- TASK-002: Read platform pain intelligence, market intelligence matrix, and global pain clusters.
- TASK-003: Identified expansion paths such as Reddit to TikTok, TikTok to SEO, YouTube to X, and Xiaohongshu to Instagram.
- TASK-004: Generated correlations with source platform, target platforms, source pain, market, reason, content fit, risk, and review flags.
- TASK-005: Added runtime outputs under `runtime/cross_platform_correlation/`.

## Test Tasks

- TEST-001: Added `tests/cross_platform_correlation_expansion_smoke_test.py`.
- TEST-002: Verified at least 5 correlations are generated.
- TEST-003: Verified every correlation has source and target platforms.
- TEST-004: Verified every correlation has `auto_publish_allowed=false`.
- TEST-005: Verified high-risk correlations require review.
- TEST-006: Verified no publish tasks are created.

## Review Tasks

- REVIEW-001: User can see source and target platform expansion paths.
- REVIEW-002: User can see why each pain can expand across platforms.
- REVIEW-003: User can see expansion fit and risk level.
- REVIEW-004: User can see publishing remains blocked.
