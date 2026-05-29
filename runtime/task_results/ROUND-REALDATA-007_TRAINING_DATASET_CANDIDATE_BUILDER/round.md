# ROUND-REALDATA-007_TRAINING_DATASET_CANDIDATE_BUILDER

## Round Goal

Build a replayable training dataset candidate from privacy-filtered and normalized real-data samples.

## Scope

This round creates candidate-only dataset artifacts for audit and review. It groups normalized social signals, excludes unsafe records, reports duplication and novelty, and creates replay instructions.

## Safety Boundary

- Dataset candidate only.
- Do not start training.
- Do not include sensitive PII.
- Do not include private messages.
- Every candidate record must have lineage.
- Every dataset must be replayable.
- Provider execution, memory writeback, promotion, platform writeback, and user contact remain blocked.

## Outputs

- `schemas/training_dataset_candidate.schema.json`
- `runtime/training_candidates/TRAINING_DATASET_CANDIDATE_POLICY.json`
- `runtime/training_candidates/TRAINING_DATASET_CANDIDATE_MANIFEST.json`
- `runtime/training_candidates/DUPLICATION_AND_NOVELTY_REPORT.json`
- `runtime/training_candidates/DATASET_REPLAY_MANIFEST.json`
- `runtime/training_candidates/TRAINING_DATASET_CANDIDATE_EVIDENCE.json`
