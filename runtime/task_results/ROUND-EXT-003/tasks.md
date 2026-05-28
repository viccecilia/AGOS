# ROUND-EXT-003 Tasks

## Execution Tasks

- TASK-001: Add `services/manual_external_feedback_intake.py`.
- TASK-002: Support manual views, likes, replies, saves, comments, and rejection reason.
- TASK-003: Persist manual feedback records with `feedback_source=manual_import`.
- TASK-004: Connect evidence-approved feedback to `PromotionFeedbackLearning`.
- TASK-005: Block no-evidence feedback from learning memory.
- TASK-006: Add Control Center panel for manual external feedback intake.

## Test Tasks

- TEST-001: Add `tests/manual_external_feedback_intake_smoke_test.py`.
- TEST-002: Run `python tests\promotion_feedback_learning_smoke_test.py`.
- TEST-003: Run `python tests\war_room_runtime_ui_smoke_test.py`.

## Review Tasks

- REVIEW-001: User can see feedback can be imported and traced.
- REVIEW-002: User can see rejected or no-evidence feedback is blocked from learning.
- REVIEW-003: User can see sample/manual/real external feedback boundaries.
