# ROUND-API-COLLECT-005

## Round Name

AGOS_LIVE_DATA_NORMALIZATION_PIPELINE

## Phase

CONTROLLED_API_INTELLIGENCE_COLLECTION

## Goal

Build Live Data Normalization Pipeline so AGOS can understand TikTok trend, Reddit topic, YouTube search, and X signal intelligence through one shared data model.

## Required Fields

- platform
- source_url
- language
- market
- pain_points
- emotion_tags
- trend_strength
- training_value_score
- source_confidence

## Scope

Allowed:

- `services/live_data_normalization_pipeline.py`
- `tests/live_data_normalization_pipeline_smoke_test.py`
- `runtime/normalized_live_data/`
- `runtime/task_results/ROUND-API-COLLECT-005/`
- `docs/project_control_center.html`

Forbidden:

- write-side platform API calls
- automatic posting, replies, DMs, follows, likes
- login automation
- platform-limit bypass
