# ROUND-REALDATA-007_TRAINING_DATASET_CANDIDATE_BUILDER Summary

## 修改了什么

- Added `services/training_dataset_candidate_builder.py`.
- Added `schemas/training_dataset_candidate.schema.json`.
- Added `tests/training_dataset_candidate_builder_smoke_test.py`.
- Generated candidate-only runtime artifacts under `runtime/training_candidates/`.
- Updated `docs/project_control_center.html` with Training Dataset Candidate status, grouping, duplication / novelty, replay manifest, exclusions, and blocked training/provider/memory states.

## 每个任务状态

- TASK-001 schema: done.
- TASK-002 grouping dimensions: done.
- TASK-003 duplication and novelty logic: done.
- TASK-004 stage transition signal: done.
- TASK-005 replay manifest: done.

## 验证结果

- `python -m compileall services schemas tests` passed.
- `python tests\training_dataset_candidate_builder_smoke_test.py` passed.
- `python tests\social_signal_normalization_smoke_test.py` passed.
- `python tests\sample_ingestion_privacy_filter_smoke_test.py` passed.
- `python tests\war_room_runtime_ui_smoke_test.py` passed.
- Browser verification passed: Control Center renders Training Dataset Candidate, TDC records, grouping dimensions, duplication / novelty report, replay manifest, unsafe exclusions, and blocked Training / Provider / Memory writeback states.

## 协作验收结果

- Control Center now exposes the candidate dataset, excluded unsafe records, duplication / novelty report, replay instructions, and explicit training-blocked state.

## 未完成 / 风险

- This is a dataset candidate only. It is not training authorization.
- Sample size remains small and must pass a later quality / bias review before any supervised training gate.

## 下一轮建议

Run `ROUND-REALDATA-008_DATASET_QUALITY_AND_BIAS_REVIEW` to evaluate platform, language, market, pain-category, confidence, and exclusion bias before any supervised dry-run or training permission round.
