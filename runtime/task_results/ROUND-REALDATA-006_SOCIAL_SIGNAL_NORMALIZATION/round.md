# ROUND-REALDATA-006_SOCIAL_SIGNAL_NORMALIZATION

## Round Goal

Normalize privacy-filtered social platform samples into comparable AGOS intelligence records.

## Scope

This round defines the normalized social signal schema, engagement normalization, content signal normalization, quality scoring, and noise / unsafe filtering.

## Safety Boundary

- No training.
- No promotion.
- No platform writeback.
- No user contact.
- No real API calls.
- Records remain replayable, auditable, sample-only, and human-review required.

## Outputs

- `schemas/social_signal_record.schema.json`
- `runtime/real_data_samples/SOCIAL_SIGNAL_NORMALIZATION_POLICY.json`
- `runtime/real_data_samples/NORMALIZED_SOCIAL_SIGNAL_SAMPLE.json`
- `runtime/real_data_samples/SIGNAL_QUALITY_SCORING_POLICY.json`
- `runtime/real_data_samples/SIGNAL_NOISE_FILTER_REPORT.json`
- `runtime/real_data_samples/SOCIAL_SIGNAL_NORMALIZATION_EVIDENCE.json`
