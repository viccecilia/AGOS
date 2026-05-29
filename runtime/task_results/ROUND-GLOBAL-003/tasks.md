# ROUND-GLOBAL-003 Tasks

## Execution Tasks

- TASK-001: Added `services/platform_pain_intelligence.py`.
- TASK-002: Read `global_pain_clusters.json` and `global_intelligence_records.json`.
- TASK-003: Supported Reddit, TikTok, Instagram, YouTube, X, Threads, SEO / Search, and Xiaohongshu.
- TASK-004: Generated platform profiles with pain points, language style, emotion, question format, content fit, risks, safe CTA, and review flags.
- TASK-005: Added runtime outputs under `runtime/platform_pain_intelligence/`.
- TASK-006: Added Control Center Platform Pain Intelligence panel.

## Test Tasks

- TEST-001: Added `tests/platform_pain_intelligence_smoke_test.py`.
- TEST-002: Verified at least 6 platforms are covered.
- TEST-003: Verified Reddit does not default to strong marketing.
- TEST-004: Verified TikTok uses short-rhythm pain expression.
- TEST-005: Verified SEO / Search exposes search intent.
- TEST-006: Verified every platform requires human review and blocks automatic publishing/replies/write API.

## Review Tasks

- REVIEW-001: User can see how pain differs by platform.
- REVIEW-002: User can see each platform's language style and question format.
- REVIEW-003: User can see reply and promotion risk.
- REVIEW-004: User can see safe CTA recommendations.
