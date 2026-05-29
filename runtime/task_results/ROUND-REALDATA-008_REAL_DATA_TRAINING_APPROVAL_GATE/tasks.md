# Tasks

## Execution Tasks
- TASK-001: Validate dataset candidate completeness.
- TASK-002: Validate lineage and replay manifest.
- TASK-003: Validate privacy and PII filter results.
- TASK-004: Validate duplication and novelty report.
- TASK-005: Validate language and region coverage.
- TASK-006: Validate risk score and unsafe content exclusions.
- TASK-007: Validate human approval requirements.
- TASK-008: Generate controlled training approval decision.

## Required Outputs
- `schemas/real_data_training_approval_gate.schema.json`
- `runtime/training_candidates/REAL_DATA_TRAINING_APPROVAL_CHECKLIST.json`
- `runtime/training_candidates/DATASET_PRIVACY_VALIDATION_REPORT.json`
- `runtime/training_candidates/DATASET_REPLAY_VALIDATION_REPORT.json`
- `runtime/training_candidates/REAL_DATA_TRAINING_GATE_DECISION.json`
- `runtime/training_candidates/REAL_DATA_TRAINING_APPROVAL_EVIDENCE.json`
